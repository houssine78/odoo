# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

from odoo.fields import Command
from odoo.tests import tagged
from odoo.tools.misc import file_open

from odoo.addons.base.tests.common import HttpCaseWithUserDemo, HttpCaseWithUserPortal


@tagged('post_install', '-at_install')
class TestCustomize(HttpCaseWithUserDemo, HttpCaseWithUserPortal):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref('base.us')

        product_attribute = cls.env['product.attribute'].create({
            'name': 'Legs',
            'visibility': 'visible',
            'sequence': 10,
            'value_ids': [
                Command.create({
                    'name': 'Steel - Test',
                    'sequence': 1,
                }),
                Command.create({
                    'name': 'Aluminium',
                    'sequence': 2,
                }),
            ]
        })
        # create a template
        product_template = cls.env['product.template'].create({
            'name': 'Test Product',
            'is_published': True,
            'list_price': 750,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': product_attribute.id,
                    'value_ids': [Command.set(product_attribute.value_ids.ids)]
                })
            ],
        })

        tax = cls.env['account.tax'].create({'name': "Test tax", 'amount': 10})
        product_template.taxes_id = tax

        # set a different price on the variants to differentiate them
        product_template_attribute_values = cls.env['product.template.attribute.value'].search([
            ('product_tmpl_id', '=', product_template.id),
        ])

        for ptav in product_template_attribute_values:
            if ptav.name == "Steel - Test":
                ptav.price_extra = 0
            else:
                ptav.price_extra = 50.4

        # Update the pricelist currency regarding env.company_id currency_id in case company has changed currency with COA installation.
        website = cls.env['website'].get_current_website()
        pricelist = website.pricelist_id
        pricelist.write({'currency_id': cls.env.company.currency_id.id})

    def test_01_admin_shop_customize_tour(self):
        # Enable Variant Group
        self.env.ref('product.group_product_variant').write({'users': [(4, self.env.ref('base.user_admin').id)]})
        self.start_tour(self.env['website'].get_client_action_url('/shop?search=Test Product'), 'shop_customize', login="admin", timeout=120)

    def test_02_admin_shop_custom_attribute_value_tour(self):
        # Make sure pricelist rule exist
        self.product_attribute_1 = self.env['product.attribute'].create({
            'name': 'Legs',
            'sequence': 10,
        })
        product_attribute_value_1 = self.env['product.attribute.value'].create({
            'name': 'Steel',
            'attribute_id': self.product_attribute_1.id,
            'sequence': 1,
        })
        product_attribute_value_2 = self.env['product.attribute.value'].create({
            'name': 'Aluminium',
            'attribute_id': self.product_attribute_1.id,
            'sequence': 2,
        })
        product_attribute_2 = self.env['product.attribute'].create({
            'name': 'Color',
            'sequence': 20,
        })
        product_attribute_value_3 = self.env['product.attribute.value'].create({
            'name': 'White',
            'attribute_id': product_attribute_2.id,
            'sequence': 1,
        })
        product_attribute_value_4 = self.env['product.attribute.value'].create({
            'name': 'Black',
            'attribute_id': product_attribute_2.id,
            'sequence': 2,
        })

        # Create product template
        self.product_product_4_product_template = self.env['product.template'].create({
            'name': 'Customizable Desk (TEST)',
            'standard_price': 500.0,
            'list_price': 750.0,
        })

        # Generate variants
        self.env['product.template.attribute.line'].create([{
            'product_tmpl_id': self.product_product_4_product_template.id,
            'attribute_id': self.product_attribute_1.id,
            'value_ids': [(4, product_attribute_value_1.id), (4, product_attribute_value_2.id)],
        }, {
            'product_tmpl_id': self.product_product_4_product_template.id,
            'attribute_id': product_attribute_2.id,
            'value_ids': [(4, product_attribute_value_3.id), (4, product_attribute_value_4.id)],

        }])
        product_template = self.product_product_4_product_template

        # Add Custom Attribute
        product_attribute_value_7 = self.env['product.attribute.value'].create({
            'name': 'Custom TEST',
            'attribute_id': self.product_attribute_1.id,
            'sequence': 3,
            'is_custom': True
        })
        self.product_product_4_product_template.attribute_line_ids[0].write({'value_ids': [(4, product_attribute_value_7.id)]})

        img_content = base64.b64encode(file_open('product/static/img/product_product_11-image.png', "rb").read())
        self.product_product_11_product_template = self.env['product.template'].create({
            'name': 'Conference Chair (TEST)',
            'website_sequence': 9999, # laule
            'image_1920': img_content,
            'list_price': 16.50,
        })

        self.env['product.template.attribute.line'].create({
            'product_tmpl_id': self.product_product_11_product_template.id,
            'attribute_id': self.product_attribute_1.id,
            'value_ids': [(4, product_attribute_value_1.id), (4, product_attribute_value_2.id)],
        })
        self.product_product_11_product_template.attribute_line_ids[0].product_template_value_ids[1].price_extra = 6.40

        # Setup a second optional product
        self.product_product_1_product_template = self.env['product.template'].create({
            'name': 'Chair floor protection',
            'list_price': 12.0,
        })

        self.env['product.pricelist'].create({
            'name': 'Base Pricelist',
            'discount_policy': 'without_discount',
            'item_ids': [Command.create({
                'base': 'list_price',
                'applied_on': '1_product',
                'product_tmpl_id': product_template.id,
                'price_discount': 20,
                'min_quantity': 2,
                'compute_price': 'formula',
            })],
        })

        self.start_tour("/", 'shop_custom_attribute_value', login="admin")

    def test_03_public_tour_shop_dynamic_variants(self):
        """ The goal of this test is to make sure product variants with dynamic
        attributes can be created by the public user (when being added to cart).
        """
        product_attribute = self.env['product.attribute'].create({
            'name': "Dynamic Attribute",
            'create_variant': 'dynamic',
            'value_ids': [
                Command.create({'name': "Dynamic Value 1"}),
                Command.create({'name': "Dynamic Value 2"}),
            ]
        })

        # create the template
        product_template = self.env['product.template'].create({
            'name': 'Dynamic Product',
            'website_published': True,
            'list_price': 10,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': product_attribute.id,
                    'value_ids': [Command.set(product_attribute.value_ids.ids)]
                })
            ]
        })

        # set a different price on the variants to differentiate them
        product_template_attribute_values = self.env['product.template.attribute.value'].search([
            ('product_tmpl_id', '=', product_template.id),
        ])

        for ptav in product_template_attribute_values:
            if ptav.name == "Dynamic Value 1":
                ptav.price_extra = 10
            else:
                # 0 to not bother with the pricelist of the public user
                ptav.price_extra = 0

        self.start_tour("/", 'tour_shop_dynamic_variants')

    def test_04_portal_tour_deleted_archived_variants(self):
        """The goal of this test is to make sure deleted and archived variants
        are shown as impossible combinations.

        Using "portal" to have various users in the tests.
        """

        # create the attribute
        product_attribute = self.env['product.attribute'].create({
            'name': "My Attribute",
            'create_variant': 'always',
            'value_ids': [
                Command.create({'name': "My Value 1"}),
                Command.create({'name': "My Value 2"}),
                Command.create({'name': "My Value 3"}),
            ],
        })

        # create the template
        product_template = self.env['product.template'].create({
            'name': 'Test Product 2',
            'is_published': True,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': product_attribute.id,
                    'value_ids': [Command.set(product_attribute.value_ids.ids)]
                }),
            ],
        })

        # set a different price on the variants to differentiate them
        product_template_attribute_values = self.env['product.template.attribute.value'].search([
            ('product_tmpl_id', '=', product_template.id),
        ])

        product_template_attribute_values[0].price_extra = 10
        product_template_attribute_values[1].price_extra = 20
        product_template_attribute_values[2].price_extra = 30

        # archive first combination (first variant)
        product_template.product_variant_ids[0].active = False
        # delete second combination (which is now first variant since cache has been cleared)
        product_template.product_variant_ids[0].unlink()

        self.start_tour("/", 'tour_shop_deleted_archived_variants', login="portal")

    def test_05_demo_tour_no_variant_attribute(self):
        """The goal of this test is to make sure attributes no_variant are
        correctly added to cart.

        Using "demo" to have various users in the tests.
        """

        product_attribute_no_variant = self.env['product.attribute'].create({
            'name': "No Variant Attribute",
            'create_variant': 'no_variant',
            'value_ids': [Command.create({'name': "No Variant Value"})],
        })

        # create the template
        product_template = self.env['product.template'].create({
            'name': 'Test Product 3',
            'website_published': True,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': product_attribute_no_variant.id,
                    'value_ids': [Command.set(product_attribute_no_variant.value_ids.ids)]
                })
            ]
        })

        # set a price on the value
        product_template.attribute_line_ids.product_template_value_ids.price_extra = 10

        self.start_tour("/", 'tour_shop_no_variant_attribute', login="demo")

    def test_06_admin_list_view_b2c(self):
        self.env.ref('product.group_product_variant').write({'users': [(4, self.env.ref('base.user_admin').id)]})

        # activate b2c
        self.env['res.config.settings'].create({
            'show_line_subtotals_tax_selection': 'tax_included'
        }).execute()

        self.start_tour(self.env['website'].get_client_action_url('/shop?search=Test Product'), 'shop_list_view_b2c', login="admin")

    def test_07_editor_shop(self):
        self.env['product.pricelist'].create([
            {'name': 'Base Pricelist', 'selectable': True},
            {'name': 'Other Pricelist', 'selectable': True}
        ])
        self.start_tour("/", 'shop_editor', login="admin")

    def test_08_portal_tour_archived_variant_multiple_attributes(self):
        """The goal of this test is to make sure that an archived variant with multiple
        attributes only disabled other options if only one is missing or all are selected.

        Using "portal" to have various users in the tests.
        """

        attributes = self.env['product.attribute'].create([
            {
                'name': 'Size',
                'value_ids': [
                    Command.create({'name': 'Large'}),
                    Command.create({'name': 'Small'}),
                ],
            },
            {
                'name': 'Color',
                'value_ids': [
                    Command.create({'name': 'White'}),
                    Command.create({'name': 'Black'}),
                ],
            },
            {
                'name': 'Brand',
                'value_ids': [
                    Command.create({'name': 'Brand A'}),
                    Command.create({'name': 'Brand B'}),
                ],
            },
        ])


        product_template = self.env['product.template'].create({
            'name': 'Test Product 2',
            'is_published': True,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': attribute.id,
                    'value_ids': [Command.set(attribute.value_ids.ids)],
                }) for attribute in attributes
            ],
        })

        product_template.product_variant_ids[-1].active = False

        self.start_tour("/", 'tour_shop_archived_variant_multi', login="portal")

    def test_09_pills_variant(self):
        """The goal of this test is to make sure that you can click anywhere on a pill
        and still trigger a variant change. The radio input be visually hidden.

        Using "portal" to have various users in the tests.
        """

        attribute_size = self.env['product.attribute'].create({
            'name': 'Size',
            'create_variant': 'always',
            'display_type': 'pills',
            'value_ids': [
                Command.create({'name': 'Large'}),
                Command.create({'name': 'Small'}),
            ],
        })

        self.env['product.template'].create({
            'name': 'Test Product 2',
            'is_published': True,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': attribute_size.id,
                    'value_ids': [Command.set(attribute_size.value_ids.ids)],
                })
            ],
        })

        self.start_tour("/", 'test_09_pills_variant', login="portal")

    def test_10_multi_checkbox_attribute(self):
        attribute = self.env['product.attribute'].create([
            {
                'name': 'Options',
                'create_variant': 'no_variant',
                'display_type': 'multi',
                'value_ids': [
                    Command.create({
                        'name': 'Option 1',
                        'default_extra_price': 1,
                        'sequence': 1,
                    }),
                    Command.create({
                        'name': 'Option 2',
                        'sequence': 2,
                    }),
                    Command.create({
                        'name': 'Option 3',
                        'default_extra_price': 3,
                        'sequence': 3,
                    }),
                    Command.create({
                        'name': 'Option 4',
                        'sequence': 4,
                    }),
                ],
            },
        ])
        product_template = self.env['product.template'].create({
            'name': 'Product Multi',
            'is_published': True,
            'list_price': 750,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': attribute.id,
                    'value_ids': [Command.set(attribute.value_ids.ids)],
                }),
            ],
        })
        # set an extra price for free attribute values on the product (nothing is free)
        self.env['product.template.attribute.value'].search([
            ('product_tmpl_id', '=', product_template.id),
            ('price_extra', '=', 0),
        ]).price_extra = 2
        # set an exclusion between option 1 and option 3
        self.env['product.template.attribute.value'].search([
            ('product_tmpl_id', '=', product_template.id),
            ('price_extra', '=', 1),
        ]).exclude_for = [
            Command.create({
                'product_tmpl_id': product_template.id,
                'value_ids': [Command.set(
                    self.env['product.template.attribute.value'].search([
                        ('product_tmpl_id', '=', product_template.id),
                        ('price_extra', '=', 3)
                    ]).ids
                )],
            }),
        ]

        self.start_tour("/", 'tour_shop_multi_checkbox', login="portal")

    def test_11_shop_editor_set_product_ribbon(self):
        self.start_tour("/", 'shop_editor_set_product_ribbon', login="admin")
