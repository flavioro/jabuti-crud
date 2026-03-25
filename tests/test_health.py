from redis.exceptions import ConnectionError


def test_health(client):
    response = client.get('/api/v1/health')

    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
    assert response.json()['database'] == 'ok'
    assert response.json()['cache'] == 'ok'


def test_health_degraded_when_cache_is_unavailable(client, redis_client, monkeypatch):
    def fail_ping():
        raise ConnectionError('redis down')

    monkeypatch.setattr(redis_client, 'ping', fail_ping)
    response = client.get('/api/v1/health')

    assert response.status_code == 200
    assert response.json()['status'] == 'degraded'
    assert response.json()['database'] == 'ok'
    assert response.json()['cache'] == 'unavailable'
