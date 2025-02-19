from controllers.facebook.get import facebook_blueprint  # Import Facebook Blueprint
from controllers.instagram.get import instagram_blueprint  # Import Instagram Blueprint
from controllers.metaAds.get import meta_ads_blueprint  # Import Meta Ads Blueprint
from controllers.AdsReport.get import ads_reports_blueprint 
from controllers.InstagramAds.get import insta_ads_blueprint 
def register_routes(app):
    app.register_blueprint(facebook_blueprint)  # Register Facebook Blueprint
    app.register_blueprint(instagram_blueprint)  # Register Instagram Blueprint
    app.register_blueprint(meta_ads_blueprint)   # Register Meta Ads Blueprint
    app.register_blueprint(ads_reports_blueprint)
    app.register_blueprint(insta_ads_blueprint)    # Register Meta Ads Blueprint
