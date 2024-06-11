def test_name(service, service_json):
    assert service.name == service_json["name"]


def test_keywords(service, service_json):
    assert service.keywords == service_json["keywords"]


def test_description(service, service_json):
    assert service.description == service_json["description"]


def test_url(service, service_json):
    assert service.url == next(link["href"] for link in service_json["links"] if link["rel"] == "service")


def test_doc_url(service, service_json):
    assert service.doc_url == next(link["href"] for link in service_json["links"] if link["rel"] == "service-doc")


def test_repr(service, service_json):
    assert repr(service) == next(link["href"] for link in service_json["links"] if link["rel"] == "service")
