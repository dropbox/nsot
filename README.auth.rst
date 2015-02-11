#########
Auth Demo
#########

Until auth stuff is finished, here's how you use it.


Authenticate to get an auth_token
=================================

The secret_key is generated when a User is created. Right now there is not a
way to get this out, so you have to inspect the table using sqlite3 (ghetto!)

::

    Content-Type: application/json
    POST /api/authenticate HTTP/1.1

    {"email": "user@localhost", "secret_key": "generated when user is createde."}

For example::

    $ curl -v --header "Content-Type: application/json" -X POST --data '{"email": "jathan@localhost", "secret_key": "QAuPaiu93Mj_SbR40kT3aHfGL2q05TzId9WGsbBwzSs="}' "http://localhost:5050/api/authenticate"
    * Adding handle: conn: 0x19c69f0
    * Adding handle: send: 0
    * Adding handle: recv: 0
    * Curl_addHandleToPipeline: length: 1
    * - Conn 0 (0x19c69f0) send_pipe: 1, recv_pipe: 0
    * About to connect() to localhost port 5050 (#0)
    *   Trying ::1...
    * Connected to localhost (::1) port 5050 (#0)
    > POST /api/authenticate HTTP/1.1
    > User-Agent: curl/7.32.0
    > Host: localhost:5050
    > Accept: */*
    > Content-Type: application/json
    > Content-Length: 93
    >
    * upload completely sent off: 93 out of 93 bytes
    < HTTP/1.1 200 OK
    < Date: Wed, 18 Feb 2015 07:38:07 GMT
    < Content-Length: 336
    < Etag: "c58a44d2f6ce5ac51f1ed21ab4111d45f8fde26c"
    < Content-Type: application/json; charset=UTF-8
    * Server TornadoServer/4.0.2 is not blacklisted
    < Server: TornadoServer/4.0.2
    <
    * Connection #0 to host localhost left intact
    {"status": "ok", "data": {"auth_token": "gAAAAABU5TAY3F1kLnx0bMBwnSVARqXypGTt8Q-RNkT3fpadMraiRRZr1QYEMQ-Fe1U7F3XZb1BbhL_47IBhxwNeUCZndmEFns7KWkGLtFkNHMRzsZ96Mls="}}%

Send the auth_token with every request
======================================

Use auth_token from the authentication payload
(``payload['data']['auth_token']``), and then pass it and the email along with
every request using the ``Authorization`` header with realm ``AuthToken``.

    Authorization: AuthToken {email}:{auth_token}
    GET /api/path HTTP/1.1

For example::

    $ curl -v --header "Content-Type: application/json" --header "Authorization: AuthToken jathan@localhost:gAAAAABU5TAY3F1kLnx0bMBwnSVARqXypGTt8Q-RNkT3fpadMraiRRZr1QYEMQ-Fe1U7F3XZb1BbhL_47IBhxwNeUCZndmEFns7KWkGLtFkNHMRzsZ96Mls=" -X GET "http://localhost:5050/api/sites/1"
    * Adding handle: conn: 0x18e7010
    * Adding handle: send: 0
    * Adding handle: recv: 0
    * Curl_addHandleToPipeline: length: 1
    * - Conn 0 (0x18e7010) send_pipe: 1, recv_pipe: 0
    * About to connect() to localhost port 5050 (#0)
    *   Trying ::1...
    * Connected to localhost (::1) port 5050 (#0)
    > GET /api/sites/1 HTTP/1.1
    > User-Agent: curl/7.32.0
    > Host: localhost:5050
    > Accept: */*
    > Content-Type: application/json
    > Authorization: AuthToken jathan@dropbox.com:gAAAAABU5TAY3F1kLnx0bMBwnSVARqXypGTt8Q-RNkT3fpadMraiRRZr1QYEMQ-Fe1U7F3XZb1BbhL_47IBhxwNeUCZndmEFns7KWkGLtFkNHMRzsZ96Mls=
    >
    < HTTP/1.1 200 OK
    < Date: Wed, 18 Feb 2015 07:39:29 GMT
    < Content-Length: 96
    < Etag: "22b92081a126d8a7c0c4a60b71d6d8269beec159"
    < Content-Type: application/json; charset=UTF-8
    * Server TornadoServer/4.0.2 is not blacklisted
    < Server: TornadoServer/4.0.2
    <
    * Connection #0 to host localhost left intact
    {"status": "ok", "data": {"site": {"description": "Default site.", "id": 1, "name": "Default"}}}
