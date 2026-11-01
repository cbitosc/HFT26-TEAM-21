/**
 * CodeEditor — Monaco Editor component for Module 7.
 * Provides syntax highlighting, line numbers, indentation, shortcuts,
 * and seamless keyboard support for Python, JavaScript, and other languages.
 */

import React, { useRef } from 'react';
import Editor, { OnMount, OnChange } from '@monaco-editor/react';
import { Loader2 } from 'lucide-react';

export interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  readOnly?: boolean;
  height?: string | number;
  onPaste?: (pasteLength: number) => void;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language = 'python',
  readOnly = false,
  height = '480px',
  onPaste,
}) => {
  const editorRef = useRef<any>(null);

  // Normalize language identifier for Monaco
  const monacoLanguage = (() => {
    const lang = (language || 'python').toLowerCase();
    if (lang === 'py' || lang === 'python3') return 'python';
    if (lang === 'js') return 'javascript';
    if (lang === 'ts') return 'typescript';
    if (lang === 'c++') return 'cpp';
    return lang;
  })();

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // Detect paste events for CodeTrace telemetry (without penalizing the student)
    editor.onDidPaste((e) => {
      const range = e.range;
      const model = editor.getModel();
      if (model && range) {
        const pastedText = model.getValueInRange(range);
        if (onPaste && pastedText) {
          onPaste(pastedText.length);
        }
      }
    });

    // Custom formatting keybinding (Shift+Alt+F)
    editor.addCommand(monaco.KeyMod.Shift | monaco.KeyMod.Alt | monaco.KeyCode.KeyF, () => {
      editor.getAction('editor.action.formatDocument')?.run();
    });
  };

  const handleEditorChange: OnChange = (newVal) => {
    onChange(newVal || '');
  };

  return (
    <div className="relative w-full rounded-b-xl overflow-hidden border border-slate-700 bg-[#1e1e1e]">
      <Editor
        height={height}
        language={monacoLanguage}
        value={value}
        theme="vs-dark"
        onChange={handleEditorChange}
        onMount={handleEditorDidMount}
        loading={
          <div className="flex h-full w-full items-center justify-center bg-[#1e1e1e] text-slate-400">
            <Loader2 className="w-6 h-6 animate-spin mr-2 text-primary-400" />
            <span className="text-sm font-mono">Loading Monaco Editor...</span>
          </div>
        }
        options={{
          readOnly,
          fontSize: 14,
          fontFamily: "'Fira Code', 'Consolas', 'Courier New', monospace",
          fontLigatures: true,
          tabSize: 4,
          insertSpaces: true,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          automaticLayout: true,
          lineNumbers: 'on',
          lineNumbersMinChars: 3,
          wordWrap: 'on',
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          smoothScrolling: true,
          padding: { top: 12, bottom: 12 },
          renderLineHighlight: 'all',
          bracketPairColorization: { enabled: true },
          scrollbar: {
            vertical: 'visible',
            horizontal: 'auto',
            verticalScrollbarSize: 10,
            horizontalScrollbarSize: 10,
          },
        }}
      />
    </div>
  );
};
