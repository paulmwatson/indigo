(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // The AceEditorController manages the interaction between
  // the ace-based editor, the model, and the document editor view.
  Indigo.AceEditorController = function(options) {
    this.initialize.apply(this, arguments);
  };
  _.extend(Indigo.AceEditorController.prototype, Backbone.Events, {
    initialize: function(options) {
      var self = this;

      this.view = options.view;

      this.editor = ace.edit(this.view.$el.find(".ace-editor")[0]);
      this.editor.setTheme("ace/theme/monokai");
      this.editor.getSession().setMode("ace/mode/xml");
      this.editor.setValue();
      this.editor.$blockScrolling = Infinity;
      this.onEditorChange = _.debounce(_.bind(this.editorChanged, this), 500);

      // setup renderer
      var xsltProcessor = new XSLTProcessor();
      $.get('/static/xsl/act.xsl')
        .then(function(xml) {
          xsltProcessor.importStylesheet(xml);
          self.xsltProcessor = xsltProcessor;
        });
    },

    editFragment: function(node) {
      // edit node, a node in the XML document
      this.render();
      this.view.$el.find('.document-sheet-container').scrollTop(0);

      var xml = this.view.xmlModel.toXml(node);
      // pretty-print the xml
      xml = vkbeautify.xml(xml, 2);

      this.editor.removeListener('change', this.onEditorChange);
      this.editor.setValue(xml);
      this.editor.on('change', this.onEditorChange);
    },

    editorChanged: function() {
      this.saveChanges();
    },

    // Save the content of the XML editor into the DOM, returns a Deferred
    saveChanges: function() {
      // update the fragment content from the editor's version
      console.log('Parsing changes to XML');

      // TODO: handle errors here
      var newFragment = $.parseXML(this.editor.getValue()).documentElement;

      this.view.updateFragment(this.view.fragment, newFragment);
      this.render();

      return $.Deferred().resolve();
    },

    render: function() {
      if (this.xsltProcessor && this.view.fragment) {
        var html = this.xsltProcessor.transformToFragment(this.view.fragment, document);
        this.view.$el.find('.document-sheet').html('').get(0).appendChild(html);
      }
    },

    resize: function() {},
  });

  // The LimeEditorController manages the interaction between
  // the LIME-based editor, the model, and the document editor view.
  Indigo.LimeEditorController = function(options) {
    this.initialize.apply(this, arguments);
  };
  _.extend(Indigo.LimeEditorController.prototype, Backbone.Events, {
    initialize: function(options) {
      this.view = options.view;
      this.initialized = false;
    },

    editFragment: function(node) {
      // if we're editing the entire document,
      // strip the metadata when we next edit the 
      this.stripMeta = !node.querySelector('meta');
      this.fragmentType = node.tagName;
      this.editing = true;

      this.resize();

      // We only want to interact with the editor once the document
      // is fully loaded, which we get as a callback from the
      // application. We only setup this event handler once.
      this.loading = true;
      if (!this.initialized) {
        LIME.app.on('documentLoaded', this.documentLoaded, this);
        this.initialized = true;
      }

      var config = {
        docMarkingLanguage: "akoma2.0",
        docType: "act",
        docLocale: this.view.model.get('country'),
        docLang: "eng",
      };

      LIME.XsltTransforms.transform(
        node,
        LIME_base_url + 'languagesPlugins/akoma2.0/AknToXhtml.xsl',
        {},
        function(html) {
          config.docText = html.firstChild.outerHTML;
          LIME.app.fireEvent("loadDocument", config);
        }
      );
    },

    documentLoaded: function() {
      // document has loaded
      this.loading = false;
    },

    // Save the content of the LIME editor into the DOM, returns a Deferred
    updateFromLime: function() {
      var self = this;
      var start = new Date().getTime();
      var oldFragment = this.view.fragment;
      var deferred = $.Deferred();

      console.log('Updating XML from LIME');

      LIME.app.fireEvent("translateRequest", function(xml) {
        var stop = new Date().getTime();
        console.log('Got XML from LIME in ' + (stop-start) + ' msecs');

        // reset the changed flag
        LIME.app.getController('Editor').changed = false;

        if (self.stripMeta) {
          // We're editing just a fragment.
          // LIME inserts a meta element which we need to strip.
          var meta = xml.querySelector('meta');
          if (meta) {
            meta.remove();
          }
        }

        // LIME wraps the document in some extra stuff, just find the
        // item we started with
        xml = xml.querySelector(self.fragmentType);
        self.view.updateFragment(oldFragment, xml);

        deferred.resolve();
      }, {
        serialize: false,
      });

      return deferred;
    },

    // Save the content of the LIME editor into the DOM, returns a Deferred
    saveChanges: function() {
      if (!this.loading) {
        return this.updateFromLime();
      } else {
        return $.Deferred().resolve();
      }
    },

    resize: function() {
      LIME.app.resize();
    },
  });


  // Handle the document editor, tracking changes and saving it back to the server.
  // The model is an Indigo.DocumentContent instance.
  Indigo.DocumentEditorView = Backbone.View.extend({
    el: '#content-tab',
    events: {
      'change [value=plaintext]': 'editWithAce',
      'change [value=lime]': 'editWithLime',
      'change [name=fullscreen]': 'toggleFullscreen',
    },

    initialize: function(options) {
      this.dirty = false;
      this.editing = false;

      // the model is a documentDom model, which holds the parsed XML
      // document and is a bit different from normal Backbone models
      this.xmlModel = options.xmlModel;
      this.xmlModel.on('change', this.setDirty, this);

      // this is the raw, unparsed XML model
      this.rawModel = options.rawModel;
      this.rawModel.on('sync', this.setClean, this);

      this.tocView = options.tocView;
      this.tocView.on('item-selected', this.editTocItem, this);

      // setup the editor controllers
      this.aceEditor = new Indigo.AceEditorController({view: this});
      this.limeEditor = new Indigo.LimeEditorController({view: this});

      this.editWithAce();
    },

    editTocItem: function(item) {
      var self = this;
      this.stopEditing()
        .then(function() {
          if (item) {
            self.$el.find('.boxed-group-header h4').text(item.title);
            self.editFragment(item.element);
          }
        });
    },

    stopEditing: function() {
      if (this.activeEditor && this.editing) {
        this.editing = false;
        return this.activeEditor.saveChanges();
      } else {
        this.editing = false;
        return $.Deferred().resolve();
      }
    },

    editFragment: function(fragment) {
      if (!this.updating && fragment) {
        console.log("Editing new fragment");
        this.editing = true;
        this.fragment = fragment;
        this.activeEditor.editFragment(fragment);
      }
    },

    toggleFullscreen: function(e) {
      this.$el.toggleClass('fullscreen');
      this.activeEditor.resize();
    },

    updateFragment: function(oldNode, newNode) {
      this.updating = true;
      try {
        this.fragment = this.xmlModel.updateFragment(oldNode, newNode);
      } finally {
        this.updating = false;
      }
    },

    editWithAce: function(e) {
      var self = this;

      this.stopEditing()
        .then(function() {
          self.$el.find('.plaintext-editor').addClass('in');
          self.$el.find('.lime-editor').removeClass('in');
          self.activeEditor = self.aceEditor;
          self.editFragment(self.fragment);
        });
    },

    editWithLime: function(e) {
      var self = this;

      this.stopEditing()
        .then(function() {
          self.$el.find('.plaintext-editor').removeClass('in');
          self.$el.find('.lime-editor').addClass('in');
          self.activeEditor = self.limeEditor;
          self.editFragment(self.fragment);
        });
    },

    setDirty: function() {
      if (!this.dirty) {
        this.dirty = true;
        this.trigger('dirty');
      }
    },

    setClean: function() {
      if (this.dirty) {
        this.dirty = false;
        this.trigger('clean');
      }
    },

    // Save the content of the editor, returns a Deferred
    save: function() {
      var self = this;

      // don't do anything if it hasn't changed
      if (!this.dirty) {
        return $.Deferred().resolve();
      }

      if (this.activeEditor) {
        // save changes from the editor, then save the model, which resolves
        // this deferred
        var wait = $.Deferred();

        this.activeEditor
          // ask the editor to returns its contents
          .saveChanges()
          .fail(function() { wait.fail(); })
          .then(function() {
            // save the model
            self.saveModel()
              .then(function() { wait.resolve(); })
              .fail(function() { wait.fail(); });
          });

        return wait;
      } else {
        return this.saveModel();
      }
    },

    // Save the content of the raw XML model, returns a Deferred
    saveModel: function() {
      // serialize the DOM into the raw model
      this.rawModel.set('content', this.xmlModel.toXml());
      return this.rawModel.save();
    },
  });
})(window);
