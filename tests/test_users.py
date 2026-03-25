from redis.exceptions import ConnectionError


def test_create_user(client):
    response = client.post(
        '/api/v1/usuarios',
        json={'nome': 'Flavio Rodrigues', 'email': 'flavio@example.com', 'idade': 30},
    )

    assert response.status_code == 201
    body = response.json()
    assert body['nome'] == 'Flavio Rodrigues'
    assert body['email'] == 'flavio@example.com'
    assert body['idade'] == 30
    assert 'id' in body


def test_list_users_with_pagination(client):
    client.post('/api/v1/usuarios', json={'nome': 'Ana Silva', 'email': 'ana@example.com', 'idade': 28})
    client.post('/api/v1/usuarios', json={'nome': 'Bruno Lima', 'email': 'bruno@example.com', 'idade': 34})

    response = client.get('/api/v1/usuarios?limit=1&offset=0')

    assert response.status_code == 200
    body = response.json()
    assert body['limit'] == 1
    assert body['offset'] == 0
    assert body['total'] == 2
    assert len(body['items']) == 1


def test_duplicate_email_returns_conflict(client):
    payload = {'nome': 'Ana Silva', 'email': 'ana@example.com', 'idade': 28}

    first = client.post('/api/v1/usuarios', json=payload)
    second = client.post('/api/v1/usuarios', json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()['detail'] == 'Email já cadastrado'


def test_get_user_by_id(client):
    create_response = client.post(
        '/api/v1/usuarios',
        json={'nome': 'Carlos Souza', 'email': 'carlos@example.com', 'idade': 40},
    )
    user_id = create_response.json()['id']

    response = client.get(f'/api/v1/usuarios/{user_id}')

    assert response.status_code == 200
    assert response.json()['id'] == user_id


def test_update_user_invalidates_cache(client, redis_client):
    create_response = client.post(
        '/api/v1/usuarios',
        json={'nome': 'Daniela Costa', 'email': 'daniela@example.com', 'idade': 29},
    )
    user_id = create_response.json()['id']

    client.get('/api/v1/usuarios?limit=10&offset=0')
    client.get(f'/api/v1/usuarios/{user_id}')
    assert len(list(redis_client.scan_iter(match='users:*'))) >= 1

    response = client.put(
        f'/api/v1/usuarios/{user_id}',
        json={'nome': 'Daniela Costa Atualizada', 'idade': 30},
    )

    assert response.status_code == 200
    assert list(redis_client.scan_iter(match='users:*')) == []


def test_delete_user(client):
    create_response = client.post(
        '/api/v1/usuarios',
        json={'nome': 'Eduardo Rocha', 'email': 'eduardo@example.com', 'idade': 31},
    )
    user_id = create_response.json()['id']

    delete_response = client.delete(f'/api/v1/usuarios/{user_id}')
    get_response = client.get(f'/api/v1/usuarios/{user_id}')

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_crud_continues_working_when_redis_fails(client, redis_client, monkeypatch):
    def fail_get(*args, **kwargs):
        raise ConnectionError('redis down on get')

    def fail_setex(*args, **kwargs):
        raise ConnectionError('redis down on set')

    def fail_scan_iter(*args, **kwargs):
        raise ConnectionError('redis down on scan')

    monkeypatch.setattr(redis_client, 'get', fail_get)
    monkeypatch.setattr(redis_client, 'setex', fail_setex)
    monkeypatch.setattr(redis_client, 'scan_iter', fail_scan_iter)

    create_response = client.post(
        '/api/v1/usuarios',
        json={'nome': 'Helena Martins', 'email': 'helena@example.com', 'idade': 27},
    )
    assert create_response.status_code == 201
    user_id = create_response.json()['id']

    get_response = client.get(f'/api/v1/usuarios/{user_id}')
    assert get_response.status_code == 200
    assert get_response.json()['email'] == 'helena@example.com'

    list_response = client.get('/api/v1/usuarios?limit=10&offset=0')
    assert list_response.status_code == 200
    assert list_response.json()['total'] >= 1

    update_response = client.put(
        f'/api/v1/usuarios/{user_id}',
        json={'nome': 'Helena Martins Atualizada', 'idade': 28},
    )
    assert update_response.status_code == 200

    delete_response = client.delete(f'/api/v1/usuarios/{user_id}')
    assert delete_response.status_code == 204
