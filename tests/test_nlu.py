from jarvis.core.nlu import NaturalLanguageParser, Intent

def test_nlu_greetings():
    p = NaturalLanguageParser()
    assert p.parse("hello").intent == Intent.GREETING
    assert p.parse("hey jarvis").intent == Intent.GREETING

def test_nlu_application_launch():
    p = NaturalLanguageParser()
    res = p.parse("Open Chrome")
    assert res.intent == Intent.OPEN_APP
    assert res.tool_name == "open_application"
    assert res.params["app_name"] == "Chrome"

def test_nlu_web_urls():
    p = NaturalLanguageParser()
    res = p.parse("Open YouTube")
    assert res.intent == Intent.OPEN_URL
    assert res.tool_name == "open_url"
    assert "youtube.com" in res.params["url"]

def test_nlu_system_telemetry():
    p = NaturalLanguageParser()
    res = p.parse("How much RAM am I using?")
    assert res.intent == Intent.SYSTEM_STATUS
    assert res.tool_name == "system_status"

def test_nlu_running_processes():
    p = NaturalLanguageParser()
    res = p.parse("What applications are currently running?")
    assert res.intent == Intent.LIST_PROCESSES
    assert res.tool_name == "list_processes"

def test_nlu_file_search():
    p = NaturalLanguageParser()
    res1 = p.parse("Find my Python files")
    assert res1.intent == Intent.FIND_FILES
    assert res1.params["extension"] == ".py"

    res2 = p.parse("Search my Downloads folder for PDFs")
    assert res2.intent == Intent.FIND_FILES
    assert res2.params["search_dir"] == "Downloads"
    assert res2.params["extension"] == ".pdf"

def test_nlu_folder_creation():
    p = NaturalLanguageParser()
    res = p.parse("Create a folder called College Projects on my desktop")
    assert res.intent == Intent.CREATE_FOLDER
    assert "college projects" in res.params["path"].lower()

def test_nlu_file_creation():
    p = NaturalLanguageParser()
    res = p.parse("Make a new text file with today's study plan")
    assert res.intent == Intent.CREATE_FILE
    assert "study_plan" in res.params["path"].lower()

def test_nlu_desktop_organization():
    p = NaturalLanguageParser()
    res = p.parse("Organize my desktop")
    assert res.intent == Intent.ORGANIZE_DESKTOP
    assert res.params["preview"] is True
