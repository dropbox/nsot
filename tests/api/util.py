def assert_error(response, code):
    output = response.json()
    assert output["status"] == "error"
    assert output["error"]["code"] == code


def assert_success(response, data):
    output = response.json()
    assert output["status"] == "ok"
    assert output["data"] == data

def assert_created(response, location):
    assert response.status_code == 201
    assert response.headers["Location"] == location
