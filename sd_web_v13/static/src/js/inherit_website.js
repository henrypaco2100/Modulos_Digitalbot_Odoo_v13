odoo.define('sd_web_13.recently_viewed_inherit_other', function (require){
    var publicWidget = require('web.public.widget');

    publicWidget.registry.productsRecentlyViewedSnippet.include({
        xmlDependencies: (publicWidget.registry.productsRecentlyViewedSnippet.prototype.xmlDependencies || []).concat(
            ['/sd_web_v13/static/src/xml/website_sale_d.xml',]
        ),
        test_inombrable: function () {
            console.log('test');
        }
    });
    publicWidget.registry.productsSearchBar.include({
        xmlDependencies: (publicWidget.registry.productsSearchBar.prototype.xmlDependencies || []).concat(
            ['/sd_web_v13/static/src/xml/website_sale_search.xml',]
        ),
    });
});

