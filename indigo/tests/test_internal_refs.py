from django.test import TestCase
from lxml import etree

from cobalt import AkomaNtosoDocument, FrbrUri

from indigo.analysis.refs.sections import InternalRefsResolver, ProvisionRef, NewInternalRefsFinder
from indigo_api.tests.fixtures import document_fixture


class InternalRefsResolverTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.resolver = InternalRefsResolver()
        self.doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_1">
              <num>1.</num>
              <subsection eId="sec_1__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_1__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_1__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_1__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_2">
              <num>2.</num>
              <subsection eId="sec_2__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_2__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_2__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_2__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
        """)).root

    def test_initial(self):
        refs = self.resolver.resolve_references("Section 1", self.doc)
        self.assertEqual(refs[0], [ProvisionRef("Section 1", 0, 9, "sec_1")])

    def test_initial_no_match(self):
        self.assertEqual([], self.resolver.resolve_references("Section 3(a)", self.doc))

    def test_ambiguous(self):
        refs = self.resolver.resolve_references("(a)", self.doc)
        self.assertEqual(refs[0], [ProvisionRef("(a)", 0, 3, "sec_1__subsec_a")])

        refs = self.resolver.resolve_references("(a)(2)", self.doc)
        self.assertEqual(refs[0], [
            ProvisionRef("(a)", 0, 3, "sec_1__subsec_a"),
            ProvisionRef("(2)", 3, 6, "sec_1__subsec_a__para_2")
        ])

    def test_nested(self):
        refs = self.resolver.resolve_references("section 1(a)", self.doc)
        self.assertEqual(refs[0], [
            ProvisionRef("section 1", 0, 9, "sec_1"),
            ProvisionRef("(a)", 9, 12, "sec_1__subsec_a")
        ])

        refs = self.resolver.resolve_references("section 2(a)(2)", self.doc)
        self.assertEqual(refs[0], [
            ProvisionRef("section 2", 0, 9, "sec_2"),
            ProvisionRef("(a)", 9, 12, "sec_2__subsec_a"),
            ProvisionRef("(2)", 12, 15, "sec_2__subsec_a__para_2")
        ])

    def test_nested_truncated(self):
        refs = self.resolver.resolve_references("section 2(a)(8)", self.doc)
        self.assertEqual(refs[0], [
            ProvisionRef("section 2", 0, 9, "sec_2"),
            ProvisionRef("(a)", 9, 12, "sec_2__subsec_a"),
        ])


class NewInternalRefsFinderTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.finder = NewInternalRefsFinder()
        self.frbr_uri = FrbrUri.parse("/akn/za/act/2009/1/eng@2009-01-01")

    def test_local_sections(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in section 26, blah.</p>
                <p>As given in section 26(a), blah.</p>
                <p>As given in section 26(a)(1)(iii), blah.</p>
                <p>As given in section 26(a)(2)(iii)(bb), blah.</p>
                <p>As given in section 26(b)(b)(iii)(dd)(A), blah.</p>
                <p>As given in section 26B, blah.</p>
                <p>As given in section 26 and section 31, blah.</p>
                <p>As <i>given</i> in (we're now in a tail) section 26, blah.</p>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26B.</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
            <section eId="sec_31">
              <num>31.</num>
              <heading>More important</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in <ref href="#sec_26">section 26</ref>, blah.</p>
                <p>As given in <ref href="#sec_26__subsec_a">section 26(a)</ref>, blah.</p>
                <p>As given in <ref href="#sec_26__subsec_a__para_1">section 26(a)(1)</ref>(iii), blah.</p>
                <p>As given in <ref href="#sec_26__subsec_a__para_2">section 26(a)(2)</ref>(iii)(bb), blah.</p>
                <p>As given in <ref href="#sec_26__subsec_b">section 26(b)</ref>(b)(iii)(dd)(A), blah.</p>
                <p>As given in <ref href="#sec_26B">section 26B</ref>, blah.</p>
                <p>As given in <ref href="#sec_26">section 26</ref> and <ref href="#sec_31">section 31</ref>, blah.</p>
                <p>As <i>given</i> in (we're now in a tail) <ref href="#sec_26">section 26</ref>, blah.</p>
              </content>
            </section>
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26B.</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
            <section eId="sec_31">
              <num>31.</num>
              <heading>More important</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
        """))

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_remote_sections(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in section 26 of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>.</p>
                <p>As <b>given</b> in section 26(a), of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> blah.</p>
                <p>As given in section 26(a)(1)(iii), of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> blah.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section 26(a)(2)(iii)(bb) thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section 26(b)(b)(iii)(dd)(A), thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <i>given</i> a tail section 31, thereof.</p>
              </content>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in <ref href="/akn/za/act/2009/1/~sec_26">section 26</ref> of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>.</p>
                <p>As <b>given</b> in <ref href="/akn/za/act/2009/1/~sec_26__subsec_a">section 26(a)</ref>, of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> blah.</p>
                <p>As given in <ref href="/akn/za/act/2009/1/~sec_26__subsec_a__para_1">section 26(a)(1)</ref>(iii), of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> blah.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <ref href="/akn/za/act/2009/1/~sec_26__subsec_a__para_2">section 26(a)(2)</ref>(iii)(bb) thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <ref href="/akn/za/act/2009/1/~sec_26__subsec_b">section 26(b)</ref>(b)(iii)(dd)(A), thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <i>given</i> a tail <ref href="/akn/za/act/2009/1/~sec_31">section 31</ref>, thereof.</p>
              </content>
            </section>
        """))

        target_doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26B.</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
            <section eId="sec_31">
              <num>31.</num>
              <heading>More important</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
        """))

        # inject the remote target document fixture
        self.finder.target_root_cache = {"/akn/za/act/2009/1": target_doc.root}

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )

    def test_remote_sections_multiple(self):
        doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in section 26 and section 26(a) of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>.</p>
                <p>As <b>given</b> in section 26(a) and section 31(c), of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> blah.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section 26(a)(2)(iii)(bb), also section 31 thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> <b>and</b> section 26(b)(b)(iii)(dd)(A) and also section 31(a), thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and section 26(b)(b)(iii)(dd)(A) and <b>also</b> section 31(a), thereof.</p>
              </content>
            </section>
        """))

        expected = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_7">
              <num>7.</num>
              <heading>Active ref heading</heading>
              <content>
                <p>As given in <ref href="/akn/za/act/2009/1/~sec_26">section 26</ref> and <ref href="/akn/za/act/2009/1/~sec_26__sec_a">section 26(a)</ref> of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref>.</p>
                <p>As <b>given</b> in <ref href="/akn/za/act/2009/1/~sec_26">section 26(a)</ref> and <ref href="/akn/za/act/2009/1/~sec_26">section 31</ref>(c), of <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> blah.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <ref href="/akn/za/act/2009/1/~sec_26__sec_a">section 26(a)(2)</ref>(iii)(bb), also <ref href="/akn/za/act/2009/1/~sec_31">section 31</ref> thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> <b>and</b> <ref href="/akn/za/act/2009/1/~sec_26">section 26(b)</ref>(b)(iii)(dd)(A) and also <ref href="/akn/za/act/2009/1/~sec_31">section 31</ref>(a), thereof.</p>
                <p>Concerning <ref href="/akn/za/act/2009/1">Act 1 of 2009</ref> and <ref href="/akn/za/act/2009/1/~sec_26__sec_b">section 26(b)</ref>(b)(iii)(dd)(A) and <b>also</b> <ref href="/akn/za/act/2009/1/~sec_31">section 31</ref>(a), thereof.</p>
              </content>
            </section>
        """))

        target_doc = AkomaNtosoDocument(document_fixture(xml="""
            <section eId="sec_26">
              <num>26.</num>
              <heading>Important heading</heading>
              <subsection eId="sec_26__subsec_a">
                <num>(a)</num>
                <paragraph eId="sec_26__subsec_a__para_1">
                  <num>(1)</num>
                </paragraph>
                <paragraph eId="sec_26__subsec_a__para_2">
                  <num>(2)</num>
                </paragraph>
              </subsection>
              <subsection eId="sec_26__subsec_b">
                <num>(b)</num>
              </subsection>
            </section>
            <section eId="sec_26B">
              <num>26B.</num>
              <heading>Another important heading</heading>
              <content>
                <p>Another important provision.</p>
              </content>
            </section>
            <section eId="sec_31">
              <num>31.</num>
              <heading>More important</heading>
              <content>
                <p>Hi!</p>
              </content>
            </section>
        """))

        # inject the remote target document fixture
        self.finder.target_root_cache = {"/akn/za/act/2009/1": target_doc.root}

        actual = etree.fromstring(doc.to_xml())
        self.finder.markup_xml_matches(self.frbr_uri, actual)
        self.assertEqual(
            expected.to_xml(encoding='unicode'),
            etree.tostring(actual, encoding='unicode')
        )
