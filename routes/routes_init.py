from controllers.facebook.get import facebook_blueprint  # Import Facebook Blueprint
from controllers.instagram.get import instagram_blueprint  # Import Instagram Blueprint
from controllers.metaAds.get import meta_ads_blueprint  # Import Meta Ads Blueprint

def register_routes(app):
    app.register_blueprint(facebook_blueprint)  # Register Facebook Blueprint
    app.register_blueprint(instagram_blueprint)  # Register Instagram Blueprint
    app.register_blueprint(meta_ads_blueprint)   # Register Meta Ads Blueprint
