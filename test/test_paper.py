from .test_auth import test_client

def test_data(test_client):
    response = test_client.post('/login',
                                data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                follow_redirects=True
                                )
    response = test_client.get('/load_papers?token=test_token')
    response = test_client.get('/data?date=today')
    assert response.status_code == 200