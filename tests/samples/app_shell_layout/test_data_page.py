from uuid import UUID

from samples.app_shell_layout.pages.data_page import Project


class TestProject:
    def test_new_record_ids_are_uuid7(self):
        factory = Project.model_fields["id"].default_factory
        assert factory is not None

        first, second = factory(), factory()

        assert UUID(first).version == 7
        assert first != second


class TestQuickFilters:
    def test_page_shows_pills_and_search(self):
        from fastapi.testclient import TestClient

        from samples.app_shell_layout.main import app

        text = TestClient(app).get("/data-page").text
        assert 'role="radiogroup"' in text
        assert 'type="search"' in text
        assert 'placeholder="Name, code, owner"' in text

    def test_deep_link_filters_the_list(self):
        from fastapi.testclient import TestClient

        from samples.app_shell_layout.main import app

        text = TestClient(app).get("/data-page?view=done").text
        assert 'value="done" checked' in text
        assert "2 of 10 projects" in text
