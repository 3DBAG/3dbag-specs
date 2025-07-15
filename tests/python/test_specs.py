from bag3d.specs.resources import get_resource_file_path


def test_get_resource_file_path():
    """Can we get the path of a resource file?"""
    assert get_resource_file_path("attributes.json").is_file()
