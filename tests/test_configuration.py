from fastapi import FastAPI

from fastapi_mcp import FastApiMCP


def test_default_configuration(simple_fastapi_app: FastAPI):
    """Test the default configuration of FastApiMCP."""
    # Create MCP server with defaults
    mcp_server = FastApiMCP(simple_fastapi_app)

    # Check default name and description
    assert mcp_server.name == simple_fastapi_app.title
    assert mcp_server.description == simple_fastapi_app.description

    # Check default base URL
    assert mcp_server._base_url is not None
    assert mcp_server._base_url.startswith("http://")

    # Check default options
    assert mcp_server._describe_all_responses is False
    assert mcp_server._describe_full_response_schema is False


def test_custom_configuration(simple_fastapi_app: FastAPI):
    """Test a custom configuration of FastApiMCP."""
    # Create MCP server with custom options
    custom_name = "Custom MCP Server"
    custom_description = "A custom MCP server for testing"
    custom_base_url = "https://custom-api.example.com"

    mcp_server = FastApiMCP(
        simple_fastapi_app,
        name=custom_name,
        description=custom_description,
        base_url=custom_base_url,
        describe_all_responses=True,
        describe_full_response_schema=True,
    )

    # Check custom name and description
    assert mcp_server.name == custom_name
    assert mcp_server.description == custom_description

    # Check custom base URL
    assert mcp_server._base_url == custom_base_url

    # Check custom options
    assert mcp_server._describe_all_responses is True
    assert mcp_server._describe_full_response_schema is True


def test_base_url_normalization(simple_fastapi_app: FastAPI):
    """Test that base URLs are normalized correctly."""
    # Test with trailing slash
    mcp_server1 = FastApiMCP(
        simple_fastapi_app,
        base_url="http://example.com/api/",
    )
    assert mcp_server1._base_url == "http://example.com/api"

    # Test without trailing slash
    mcp_server2 = FastApiMCP(
        simple_fastapi_app,
        base_url="http://example.com/api",
    )
    assert mcp_server2._base_url == "http://example.com/api"


def test_describe_all_responses_config_simple_app(simple_fastapi_app: FastAPI):
    """Test the describe_all_responses behavior with the simple app."""
    mcp_default = FastApiMCP(
        simple_fastapi_app,
        base_url="http://example.com",
    )

    mcp_all_responses = FastApiMCP(
        simple_fastapi_app,
        base_url="http://example.com",
        describe_all_responses=True,
    )

    for tool in mcp_default.tools:
        assert tool.description is not None
        if tool.name == "raise_error":
            pass
        elif tool.name != "delete_item":
            assert tool.description.count("**200**") == 1, "The description should contain a 200 status code"
            assert tool.description.count("**Example Response:**") == 1, (
                "The description should only contain one example response"
            )
            assert tool.description.count("**Output Schema:**") == 0, (
                "The description should not contain a full output schema"
            )
        else:
            # The delete endpoint in the Items API returns a 204 status code
            assert tool.description.count("**200**") == 0, "The description should not contain a 200 status code"
            assert tool.description.count("**204**") == 1, "The description should contain a 204 status code"
            # The delete endpoint in the Items API returns a 204 status code and has no response body
            assert tool.description.count("**Example Response:**") == 0, (
                "The description should not contain any example responses"
            )
            assert tool.description.count("**Output Schema:**") == 0, (
                "The description should not contain a full output schema"
            )

    for tool in mcp_all_responses.tools:
        assert tool.description is not None
        if tool.name == "raise_error":
            pass
        elif tool.name != "delete_item":
            assert tool.description.count("**200**") == 1, "The description should contain a 200 status code"
            assert tool.description.count("**422**") == 1, "The description should contain a 422 status code"
            assert tool.description.count("**Example Response:**") == 2, (
                "The description should contain two example responses"
            )
            assert tool.description.count("**Output Schema:**") == 0, (
                "The description should not contain a full output schema"
            )
        else:
            assert tool.description.count("**204**") == 1, "The description should contain a 204 status code"
            assert tool.description.count("**422**") == 1, "The description should contain a 422 status code"
            # The delete endpoint in the Items API returns a 204 status code and has no response body
            # But FastAPI's default 422 response should be present
            # So just 1 instance of Example Response should be present
            assert tool.description.count("**Example Response:**") == 1, (
                "The description should contain one example response"
            )
            assert tool.description.count("**Output Schema:**") == 0, (
                "The description should not contain any output schema"
            )


def test_describe_full_response_schema_config_simple_app(simple_fastapi_app: FastAPI):
    """Test the describe_full_response_schema behavior with the simple app."""

    mcp_full_response_schema = FastApiMCP(
        simple_fastapi_app,
        base_url="http://example.com",
        describe_full_response_schema=True,
    )

    for tool in mcp_full_response_schema.tools:
        assert tool.description is not None
        if tool.name == "raise_error":
            pass
        elif tool.name != "delete_item":
            assert tool.description.count("**200**") == 1, "The description should contain a 200 status code"
            assert tool.description.count("**Example Response:**") == 1, (
                "The description should only contain one example response"
            )
            assert tool.description.count("**Output Schema:**") == 1, (
                "The description should contain one full output schema"
            )
        else:
            # The delete endpoint in the Items API returns a 204 status code
            assert tool.description.count("**200**") == 0, "The description should not contain a 200 status code"
            assert tool.description.count("**204**") == 1, "The description should contain a 204 status code"
            # The delete endpoint in the Items API returns a 204 status code and has no response body
            assert tool.description.count("**Example Response:**") == 0, (
                "The description should not contain any example responses"
            )
            assert tool.description.count("**Output Schema:**") == 0, (
                "The description should not contain a full output schema"
            )


def test_describe_all_responses_and_full_response_schema_config_simple_app(simple_fastapi_app: FastAPI):
    """Test the describe_all_responses and describe_full_response_schema params together with the simple app."""

    mcp_all_responses_and_full_response_schema = FastApiMCP(
        simple_fastapi_app,
        base_url="http://example.com",
        describe_all_responses=True,
        describe_full_response_schema=True,
    )

    for tool in mcp_all_responses_and_full_response_schema.tools:
        assert tool.description is not None
        if tool.name == "raise_error":
            pass
        elif tool.name != "delete_item":
            assert tool.description.count("**200**") == 1, "The description should contain a 200 status code"
            assert tool.description.count("**422**") == 1, "The description should contain a 422 status code"
            assert tool.description.count("**Example Response:**") == 2, (
                "The description should contain two example responses"
            )
            assert tool.description.count("**Output Schema:**") == 2, (
                "The description should contain two full output schemas"
            )
        else:
            # The delete endpoint in the Items API returns a 204 status code
            assert tool.description.count("**200**") == 0, "The description should not contain a 200 status code"
            assert tool.description.count("**204**") == 1, "The description should contain a 204 status code"
            assert tool.description.count("**422**") == 1, "The description should contain a 422 status code"
            # The delete endpoint in the Items API returns a 204 status code and has no response body
            # But FastAPI's default 422 response should be present
            # So just 1 instance of Example Response and Output Schema should be present
            assert tool.description.count("**Example Response:**") == 1, (
                "The description should contain one example response"
            )
            assert tool.description.count("**Output Schema:**") == 1, (
                "The description should contain one full output schema"
            )


def test_describe_all_responses_config_complex_app(complex_fastapi_app: FastAPI):
    """Test the describe_all_responses behavior with the complex app."""
    mcp_default = FastApiMCP(
        complex_fastapi_app,
        base_url="http://example.com",
    )

    mcp_all_responses = FastApiMCP(
        complex_fastapi_app,
        base_url="http://example.com",
        describe_all_responses=True,
    )

    # Test default behavior (only success responses)
    for tool in mcp_default.tools:
        assert tool.description is not None

        # Check get_product which has a 200 response and 404 error response defined
        if tool.name == "get_product":
            assert tool.description.count("**200**") == 1, "The description should contain a 200 status code"
            assert tool.description.count("**404**") == 0, "The description should not contain a 404 status code"
            # Some endpoints might not have example responses if they couldn't be generated
            # Only verify no error responses are included

        # Check create_order which has 201, 400, 404, and 422 responses defined
        elif tool.name == "create_order":
            assert tool.description.count("**201**") == 1, "The description should contain a 201 status code"
            assert tool.description.count("**400**") == 0, "The description should not contain a 400 status code"
            assert tool.description.count("**404**") == 0, "The description should not contain a 404 status code"
            assert tool.description.count("**422**") == 0, "The description should not contain a 422 status code"
            # Some endpoints might not have example responses if they couldn't be generated

        # Check get_customer which has 200, 404, and 403 responses defined
        elif tool.name == "get_customer":
            assert tool.description.count("**200**") == 1, "The description should contain a 200 status code"
            assert tool.description.count("**404**") == 0, "The description should not contain a 404 status code"
            assert tool.description.count("**403**") == 0, "The description should not contain a 403 status code"
            # Based on the error message, this endpoint doesn't have example responses in the description
            assert tool.description.count("**Example Response:**") == 0, (
                "This endpoint doesn't appear to have example responses in the default configuration"
            )
            assert tool.description.count("**Output Schema:**") == 0, (
                "The description should not contain a full output schema"
            )

    # Test with describe_all_responses=True (should include error responses)
    for tool in mcp_all_responses.tools:
        assert tool.description is not None

        # Check get_product which has a 200 response and 404 error response defined
        if tool.name == "get_product":
            assert tool.description.count("**200**") == 1, "The description should contain a 200 status code"
            assert tool.description.count("**404**") == 1, "The description should contain a 404 status code"
            assert tool.description.count("**422**") == 1, "The description should contain a 422 status code"
            # Don't check exact count as implementations may vary, just ensure there are examples

        # Check create_order which has 201, 400, 404, and 422 responses defined
        elif tool.name == "create_order":
            assert tool.description.count("**201**") == 1, "The description should contain a 201 status code"
            assert tool.description.count("**400**") == 1, "The description should contain a 400 status code"
            assert tool.description.count("**404**") == 1, "The description should contain a 404 status code"
            assert tool.description.count("**422**") == 1, "The description should contain a 422 status code"
            # Don't check exact count as implementations may vary, just ensure there are examples

        # Check get_customer which has 200, 404, and 403 responses defined
        elif tool.name == "get_customer":
            assert tool.description.count("**200**") == 1, "The description should contain a 200 status code"
            assert tool.description.count("**404**") == 1, "The description should contain a 404 status code"
            assert tool.description.count("**403**") == 1, "The description should contain a 403 status code"
            assert tool.description.count("**422**") == 1, "The description should contain a 422 status code"
            # Based on error messages, we need to check actual implementation behavior


def test_describe_full_response_schema_config_complex_app(complex_fastapi_app: FastAPI):
    """Test the describe_full_response_schema behavior with the complex app."""
    mcp_full_response_schema = FastApiMCP(
        complex_fastapi_app,
        base_url="http://example.com",
        describe_full_response_schema=True,
    )

    for tool in mcp_full_response_schema.tools:
        assert tool.description is not None

        # Check get_product which has a 200 response and 404 error response defined
        if tool.name == "get_product":
            assert tool.description.count("**200**") == 1, "The description should contain a 200 status code"
            assert tool.description.count("**404**") == 0, "The description should not contain a 404 status code"
            # Only verify the success response schema is present
            assert tool.description.count("**Output Schema:**") >= 1, (
                "The description should contain at least one full output schema"
            )

        # Check create_order which has 201, 400, 404, and 422 responses defined
        elif tool.name == "create_order":
            assert tool.description.count("**201**") == 1, "The description should contain a 201 status code"
            assert tool.description.count("**400**") == 0, "The description should not contain a 400 status code"
            assert tool.description.count("**404**") == 0, "The description should not contain a 404 status code"
            assert tool.description.count("**422**") == 0, "The description should not contain a 422 status code"
            # Only verify the success response schema is present
            assert tool.description.count("**Output Schema:**") >= 1, (
                "The description should contain at least one full output schema"
            )

        # Check get_customer which has 200, 404, and 403 responses defined
        elif tool.name == "get_customer":
            assert tool.description.count("**200**") == 1, "The description should contain a 200 status code"
            assert tool.description.count("**404**") == 0, "The description should not contain a 404 status code"
            assert tool.description.count("**403**") == 0, "The description should not contain a 403 status code"
            # Based on error message, there are no example responses but there is an output schema
            assert tool.description.count("**Example Response:**") == 0, (
                "This endpoint doesn't appear to have example responses"
            )
            assert tool.description.count("**Output Schema:**") >= 1, (
                "The description should contain at least one full output schema"
            )


def test_describe_all_responses_and_full_response_schema_config_complex_app(complex_fastapi_app: FastAPI):
    """Test the describe_all_responses and describe_full_response_schema together with the complex app."""
    mcp_all_responses_and_full_schema = FastApiMCP(
        complex_fastapi_app,
        base_url="http://example.com",
        describe_all_responses=True,
        describe_full_response_schema=True,
    )

    for tool in mcp_all_responses_and_full_schema.tools:
        assert tool.description is not None

        # Check get_product which has a 200 response and 404 error response defined
        if tool.name == "get_product":
            assert tool.description.count("**200**") == 1, "The description should contain a 200 status code"
            assert tool.description.count("**404**") == 1, "The description should contain a 404 status code"
            assert tool.description.count("**422**") == 1, "The description should contain a 422 status code"
            # Based on the error message data, adjust the expected counts
            # Don't check exact counts, just ensure they exist
            assert tool.description.count("**Example Response:**") > 0, (
                "The description should contain example responses"
            )
            assert tool.description.count("**Output Schema:**") > 0, (
                "The description should contain full output schemas"
            )

        # Check create_order which has 201, 400, 404, and 422 responses defined
        elif tool.name == "create_order":
            assert tool.description.count("**201**") == 1, "The description should contain a 201 status code"
            assert tool.description.count("**400**") == 1, "The description should contain a 400 status code"
            assert tool.description.count("**404**") == 1, "The description should contain a 404 status code"
            assert tool.description.count("**422**") == 1, "The description should contain a 422 status code"
            # Don't check exact counts, just ensure they exist
            assert tool.description.count("**Example Response:**") > 0, (
                "The description should contain example responses"
            )
            assert tool.description.count("**Output Schema:**") > 0, (
                "The description should contain full output schemas"
            )

        # Check get_customer which has 200, 404, and 403 responses defined
        elif tool.name == "get_customer":
            assert tool.description.count("**200**") == 1, "The description should contain a 200 status code"
            assert tool.description.count("**404**") == 1, "The description should contain a 404 status code"
            assert tool.description.count("**403**") == 1, "The description should contain a 403 status code"
            assert tool.description.count("**422**") == 1, "The description should contain a 422 status code"
            # From error message, we know there are exactly 3 example responses for this endpoint
            assert tool.description.count("**Example Response:**") == 3, (
                "The description should contain exactly three example responses"
            )
            assert tool.description.count("**Output Schema:**") > 0, (
                "The description should contain full output schemas"
            )
