import re

from playwright.sync_api import expect

from umap.models import DataLayer, Map

from ..base import DataLayerFactory


def test_should_have_fieldset_for_layer_type_properties(page, live_server, tilelayer):
    page.goto(f"{live_server.url}/en/map/new/")

    # Open DataLayers list
    button = page.get_by_title("Manage Layers")
    expect(button).to_be_visible()
    button.click()

    # Create a layer
    page.get_by_title("Manage layers").click()
    page.get_by_role("button", name="Add a layer").click()
    page.locator("input[name=name]").fill("Layer 1")

    select = page.locator("#umap-ui-container .umap-field-type select")
    expect(select).to_be_visible()

    choropleth_header = page.get_by_text("Choropleth: settings")
    heat_header = page.get_by_text("Heatmap: settings")
    cluster_header = page.get_by_text("Clustered: settings")
    expect(choropleth_header).to_be_hidden()
    expect(heat_header).to_be_hidden()
    expect(cluster_header).to_be_hidden()

    # Switching to Choropleth should add a dedicated fieldset
    select.select_option("Choropleth")
    expect(choropleth_header).to_be_visible()
    expect(heat_header).to_be_hidden()
    expect(cluster_header).to_be_hidden()

    select.select_option("Heat")
    expect(heat_header).to_be_visible()
    expect(choropleth_header).to_be_hidden()
    expect(cluster_header).to_be_hidden()

    select.select_option("Cluster")
    expect(cluster_header).to_be_visible()
    expect(choropleth_header).to_be_hidden()
    expect(heat_header).to_be_hidden()

    select.select_option("Default")
    expect(choropleth_header).to_be_hidden()
    expect(heat_header).to_be_hidden()
    expect(cluster_header).to_be_hidden()


def test_cancel_deleting_datalayer_should_restore(
    live_server, map, login, datalayer, page
):
    # Faster than doing a login
    map.edit_status = Map.ANONYMOUS
    map.save()
    page.goto(f"{live_server.url}{map.get_absolute_url()}?edit")
    layers = page.locator(".umap-browse-datalayers li")
    markers = page.locator(".leaflet-marker-icon")
    expect(layers).to_have_count(1)
    expect(markers).to_have_count(1)
    page.get_by_role("link", name="Manage layers").click()
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#umap-ui-container").get_by_title("Delete layer").click()
    expect(markers).to_have_count(0)
    page.get_by_role("button", name="See data layers").click()
    expect(page.get_by_text("test datalayer")).to_be_hidden()
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Cancel edits").click()
    expect(markers).to_have_count(1)
    expect(
        page.locator(".leaflet-control-browse").get_by_text("test datalayer")
    ).to_be_visible()


def test_can_clone_datalayer(live_server, map, login, datalayer, page):
    # Faster than doing a login
    map.edit_status = Map.ANONYMOUS
    map.save()
    page.goto(f"{live_server.url}{map.get_absolute_url()}?edit")
    layers = page.locator(".umap-browse-datalayers li")
    markers = page.locator(".leaflet-marker-icon")
    expect(layers).to_have_count(1)
    expect(markers).to_have_count(1)
    page.get_by_role("link", name="Manage layers").click()
    page.locator("#umap-ui-container").get_by_title("Edit", exact=True).click()
    page.get_by_role("heading", name="Advanced actions").click()
    page.get_by_role("button", name="Clone").click()
    expect(layers).to_have_count(2)
    expect(markers).to_have_count(2)


def test_can_change_icon_class(live_server, map, page):
    # Faster than doing a login
    data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Point 4"},
                "geometry": {"type": "Point", "coordinates": [0.856934, 45.290347]},
            },
        ],
    }
    DataLayerFactory(map=map, data=data)
    map.edit_status = Map.ANONYMOUS
    map.save()
    page.goto(f"{live_server.url}{map.get_absolute_url()}?edit")
    expect(page.locator(".umap-div-icon")).to_be_visible()
    page.get_by_role("link", name="Manage layers").click()
    expect(page.locator(".umap-circle-icon")).to_be_hidden()
    page.locator("#umap-ui-container").get_by_title("Edit", exact=True).click()
    page.get_by_role("heading", name="Shape properties").click()
    page.locator(".umap-field-iconClass a.define").click()
    page.get_by_text("Circle").click()
    expect(page.locator(".umap-circle-icon")).to_be_visible()
    expect(page.locator(".umap-div-icon")).to_be_hidden()


def test_can_change_name(live_server, map, page, datalayer):
    map.edit_status = Map.ANONYMOUS
    map.save()
    page.goto(
        f"{live_server.url}{map.get_absolute_url()}?edit&datalayersControl=expanded"
    )
    page.get_by_role("link", name="Manage layers").click()
    page.locator("#umap-ui-container").get_by_title("Edit", exact=True).click()
    expect(page.locator(".umap-is-dirty")).to_be_hidden()
    page.locator('input[name="name"]').click()
    page.locator('input[name="name"]').press("Control+a")
    page.locator('input[name="name"]').fill("new name")
    expect(page.locator(".leaflet-control-browse li span")).to_contain_text("new name")
    expect(page.locator(".umap-is-dirty")).to_be_visible()
    with page.expect_response(re.compile(".*/datalayer/update/.*")):
        page.get_by_role("button", name="Save").click()
    saved = DataLayer.objects.last()
    assert saved.name == "new name"
    expect(page.locator(".umap-is-dirty")).to_be_hidden()


def test_can_create_new_datalayer(live_server, map, page, datalayer):
    map.edit_status = Map.ANONYMOUS
    map.save()
    page.goto(
        f"{live_server.url}{map.get_absolute_url()}?edit&datalayersControl=expanded"
    )
    page.get_by_role("link", name="Manage layers").click()
    page.get_by_role("button", name="Add a layer").click()
    page.locator('input[name="name"]').click()
    page.locator('input[name="name"]').fill("my new layer")
    expect(page.get_by_text("my new layer")).to_be_visible()
    with page.expect_response(re.compile(".*/datalayer/create/.*")):
        page.get_by_role("button", name="Save").click()
    assert DataLayer.objects.count() == 2
    saved = DataLayer.objects.last()
    assert saved.name == "my new layer"
    expect(page.locator(".umap-is-dirty")).to_be_hidden()
    # Edit again, it should not create a new datalayer
    page.get_by_role("link", name="Manage layers").click()
    page.locator("#umap-ui-container").get_by_title("Edit", exact=True).first.click()
    page.locator('input[name="name"]').click()
    page.locator('input[name="name"]').fill("my new layer with a new name")
    expect(page.get_by_text("my new layer with a new name")).to_be_visible()
    page.get_by_role("button", name="Save").click()
    with page.expect_response(re.compile(".*/datalayer/update/.*")):
        page.get_by_role("button", name="Save").click()
    assert DataLayer.objects.count() == 2
    saved = DataLayer.objects.last()
    assert saved.name == "my new layer with a new name"
    expect(page.locator(".umap-is-dirty")).to_be_hidden()


def test_can_restore_version(live_server, map, page, datalayer):
    map.edit_status = Map.ANONYMOUS
    map.save()
    page.goto(f"{live_server.url}{map.get_absolute_url()}?edit")
    marker = page.locator(".leaflet-marker-icon")
    expect(marker).to_have_class(re.compile(".*umap-ball-icon.*"))
    marker.click(modifiers=["Shift"])
    page.get_by_role("heading", name="Shape properties").click()
    page.locator("#umap-feature-shape-properties").get_by_text("Default").click()
    with page.expect_response(re.compile(".*/datalayer/update/.*")):
        page.get_by_role("button", name="Save").click()
    expect(marker).to_have_class(re.compile(".*umap-div-icon.*"))
    page.get_by_role("link", name="Manage layers").click()
    page.locator("#umap-ui-container").get_by_title("Edit", exact=True).click()
    page.get_by_role("heading", name="Versions").click()
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("button", name="Restore this version").last.click()
    expect(marker).to_have_class(re.compile(".*umap-ball-icon.*"))
