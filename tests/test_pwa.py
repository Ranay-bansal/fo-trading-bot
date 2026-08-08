import unittest
import json
import os

class TestPWAAndDeployment(unittest.TestCase):
    """
    Tier 1 & Tier 2 Test Suite for PWA Compliance & Vercel Static Deployment Paths.
    Covers manifest.json specs, Service Worker offline caching, static icon assets,
    vercel.json configuration, HTML meta tags, and relative path resolutions.
    """

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_manifest_json_root_exists(self):
        """Test 1: Manifest files exist in public/ and dashboard/ directories."""
        public_manifest = os.path.join(self.base_dir, "public", "manifest.json")
        dashboard_manifest = os.path.join(self.base_dir, "dashboard", "manifest.json")
        self.assertTrue(os.path.exists(public_manifest))
        self.assertTrue(os.path.exists(dashboard_manifest))

    def test_manifest_json_required_fields(self):
        """Test 2: Manifest contains valid required PWA schema properties."""
        manifest_path = os.path.join(self.base_dir, "public", "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        required_keys = ["name", "short_name", "start_url", "display", "icons", "theme_color", "background_color"]
        for key in required_keys:
            self.assertIn(key, data)

        self.assertEqual(data["display"], "standalone")
        self.assertEqual(len(data["icons"]), 4)

    def test_manifest_icons_existence(self):
        """Test 3: Icon PNG files referenced in manifest exist on disk."""
        icon192_public = os.path.join(self.base_dir, "public", "icon-192.png")
        icon512_public = os.path.join(self.base_dir, "public", "icon-512.png")
        self.assertTrue(os.path.exists(icon192_public))
        self.assertTrue(os.path.exists(icon512_public))

    def test_service_worker_script_exists(self):
        """Test 4: Service Worker sw.js exists in public/ and dashboard/."""
        sw_public = os.path.join(self.base_dir, "public", "sw.js")
        sw_dashboard = os.path.join(self.base_dir, "dashboard", "sw.js")
        self.assertTrue(os.path.exists(sw_public))
        self.assertTrue(os.path.exists(sw_dashboard))

    def test_service_worker_events(self):
        """Test 5: Service worker contains install, activate, and fetch handlers."""
        sw_path = os.path.join(self.base_dir, "public", "sw.js")
        with open(sw_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("install", content)
        self.assertIn("activate", content)
        self.assertIn("fetch", content)
        self.assertIn("shadow-traders-v5", content)

    def test_vercel_json_validity(self):
        """Test 6: vercel.json is valid JSON configuration."""
        vercel_path = os.path.join(self.base_dir, "vercel.json")
        self.assertTrue(os.path.exists(vercel_path))
        with open(vercel_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("version", data)

    def test_static_assets_all_directories(self):
        """Test 7: Static branding assets exist across public/ and dashboard/."""
        dirs = ["public", "dashboard"]
        assets = ["logo.jpg", "background.jpg", "icon-192.png", "icon-512.png"]
        for d in dirs:
            for asset in assets:
                p = os.path.join(self.base_dir, d, asset)
                self.assertTrue(os.path.exists(p), f"Missing asset: {p}")

    def test_html_pwa_head_meta_tags(self):
        """Test 8: index.html head contains PWA meta tags and manifest link."""
        index_path = os.path.join(self.base_dir, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('<link rel="manifest"', content)
        self.assertIn('<meta name="theme-color"', content)
        self.assertIn('<meta name="apple-mobile-web-app-capable"', content)

    def test_service_worker_registration_script(self):
        """Test 9: index.html contains navigator.serviceWorker.register code."""
        index_path = os.path.join(self.base_dir, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("serviceWorker", content)
        self.assertIn("register(", content)

    def test_manifest_start_url_relative(self):
        """Test 10 (Boundary): Manifest start_url is relative to prevent Vercel 404s."""
        manifest_path = os.path.join(self.base_dir, "public", "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertTrue(data["start_url"].startswith("./"))

    def test_service_worker_fetch_handler_get_only(self):
        """Test 11 (Boundary): Service Worker fetch handler filters non-GET requests."""
        sw_path = os.path.join(self.base_dir, "public", "sw.js")
        with open(sw_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("e.request.method !== 'GET'", content)

    def test_html_image_fallback_attributes(self):
        """Test 12 (Boundary): Branding image tags include onerror fallback attribute."""
        index_path = os.path.join(self.base_dir, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('onerror="this.src=\'logo.jpg\'"', content)

if __name__ == "__main__":
    unittest.main()
