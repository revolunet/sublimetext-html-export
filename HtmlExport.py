import sublime, sublime_plugin
import webbrowser
import tempfile
import os
import json

settings = sublime.load_settings('HtmlExport.sublime-settings')

LANGUAGES = {
    'c': 'clike',
    'cc': 'clike',
    'cpp': 'clike',
    'cs': 'clike',
    'coffee': 'coffeescript',
    'css': 'css',
    'diff': 'diff',
    'go': 'go',
    'html': 'htmlmixed',
    'htm': 'htmlmixed',
    'js': 'javascript',
    'json': 'javascript',
    'less': 'less',
    'lua': 'lua',
    'md': 'markdown',
    'markdown': 'markdown',
    'pl': 'perl',
    'php': 'php',
    'py': 'python',
    'pl': 'perl',
    'rb': 'ruby',
    'xml': 'xml',
    'xsl': 'xml',
    'xslt': 'xml'
}

DEPENDENCIES = {
    'php': ['xml', 'javascript', 'css', 'clike'],
    'markdown': ['xml'],
    'htmlmixed': ['xml', 'javascript', 'css']
}


class HtmlExportCommand(sublime_plugin.TextCommand):
    """ Export file contents to a single HTML file"""
    def run(self, edit):
        region = sublime.Region(0, self.view.size())
        encoding = self.view.encoding()
        if encoding == 'Undefined':
            encoding = 'UTF-8'
        elif encoding == 'Western (Windows 1252)':
            encoding = 'windows-1252'
        contents = self.view.substr(region)
        contents = contents.replace('<', '&lt;').replace('>', '&gt;')
        tmp_html = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
        tmp_html.write('<meta charset="%s">' % self.view.encoding())
        # package manager path
        plugin_dir = os.path.join(sublime.packages_path(), 'HTML Export')
        if not os.path.isdir(plugin_dir):
            # git dir
            plugin_dir = os.path.join(sublime.packages_path(), 'sublimetext-html-export')
            if not os.path.isdir(plugin_dir):
                raise Exception("ERROR: cant find codemirror dir !")
        filename = self.view.file_name()
        language = None
        if filename:
            fileext = os.path.splitext(filename)[1][1:]
            language = LANGUAGES.get(fileext.lower())
        else:
            filename = 'unamed file'
        js = open(os.path.join(plugin_dir, 'codemirror', 'lib', 'codemirror.js'), 'r').read()
        if language:
            for dependency in DEPENDENCIES.get(language, []):
                js += open(os.path.join(plugin_dir, 'codemirror', 'mode', dependency, '%s.js' % dependency), 'r').read()
            js += open(os.path.join(plugin_dir, 'codemirror', 'mode', language, '%s.js' % language), 'r').read()
        css = open(os.path.join(plugin_dir, 'codemirror', 'lib', 'codemirror.css'), 'r').read()

        editorConfig = {
            'mode': language,
            'lineNumbers': True
        }

        user_editorConfig = settings.get('editorConfig')
        if user_editorConfig and isinstance(user_editorConfig, dict):
            editorConfig.update(user_editorConfig)

        theme = editorConfig.get('theme')
        if theme:
            theme_css = os.path.join(plugin_dir, 'codemirror', 'theme', '%s.css' % theme)
            if os.path.isfile(theme_css):
                css += open(theme_css, 'r').read()

        datas = {
             'title': os.path.basename(filename),
             'css': css,
             'js': js,
             'code': contents,
             'editorConfig': json.dumps(editorConfig)
        }

        html = u"""
            <!doctype html>
            <html>
              <head>
                <title>%(title)s</title>
                <script>%(js)s</script>
                <style>%(css)s</style>
                <style>.CodeMirror-scroll {height: auto; overflow: visible;}</style>
              </head>
              <body>
                <h3>%(title)s</h3>
                <textarea id="code" name="code">%(code)s</textarea>
                <script>
                var editor = CodeMirror.fromTextArea(document.getElementById("code"), %(editorConfig)s);
                </script>
              </body>
            </html>
        """ % datas
        tmp_html.write(html.encode(encoding))
        tmp_html.close()
        webbrowser.open_new_tab(tmp_html.name)
