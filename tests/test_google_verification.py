import app as app_module


def test_google_site_verification_file_is_served_from_the_site_root():
    response = app_module.app.test_client().get("/google05c3788b5b10db5e.html")

    assert response.status_code == 200
    assert response.get_data(as_text=True).strip() == (
        "google-site-verification: google05c3788b5b10db5e.html"
    )
