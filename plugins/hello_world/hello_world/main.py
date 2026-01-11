class PluginMain:
    def __init__(self):
        self.name = "Hello World"
        self.version = "1.0.0"

    def on_enable(self):
        print("👋 Hello World Plugin Enabled!")

    def hello(self, name="User"):
        return f"Hello, {name}! This is the AMA-Intent Plugin System."
