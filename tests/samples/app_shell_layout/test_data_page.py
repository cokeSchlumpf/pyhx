from uuid import UUID

from samples.app_shell_layout.pages.data_page import Project


class TestProject:
    def test_new_record_ids_are_uuid7(self):
        factory = Project.model_fields["id"].default_factory
        assert factory is not None

        first, second = factory(), factory()

        assert UUID(first).version == 7
        assert first != second
