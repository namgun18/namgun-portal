<script setup lang="ts">
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Link from '@tiptap/extension-link'

const props = defineProps<{
  initialContent?: string
}>()

const text = defineModel<string>('text', { default: '' })
const html = defineModel<string | null>('html', { default: null })

const editor = useEditor({
  extensions: [
    StarterKit,
    Underline,
    Link.configure({ openOnClick: false }),
  ],
  content: props.initialContent || '',
  onUpdate: ({ editor: e }) => {
    html.value = e.getHTML()
    text.value = e.getText()
  },
})

watch(() => props.initialContent, (content) => {
  if (editor.value && content !== undefined) {
    const current = editor.value.getText()
    if (!current && content) {
      editor.value.commands.setContent(content)
    }
  }
})

function toggleBold() { editor.value?.chain().focus().toggleBold().run() }
function toggleItalic() { editor.value?.chain().focus().toggleItalic().run() }
function toggleUnderline() { editor.value?.chain().focus().toggleUnderline().run() }
function toggleStrike() { editor.value?.chain().focus().toggleStrike().run() }
function toggleH1() { editor.value?.chain().focus().toggleHeading({ level: 1 }).run() }
function toggleH2() { editor.value?.chain().focus().toggleHeading({ level: 2 }).run() }
function toggleBulletList() { editor.value?.chain().focus().toggleBulletList().run() }
function toggleOrderedList() { editor.value?.chain().focus().toggleOrderedList().run() }
function toggleBlockquote() { editor.value?.chain().focus().toggleBlockquote().run() }
function toggleCode() { editor.value?.chain().focus().toggleCodeBlock().run() }

function setLink() {
  const url = window.prompt('링크 URL을 입력하세요:')
  if (url) {
    editor.value?.chain().focus().setLink({ href: url }).run()
  }
}

function isActive(name: string, attrs?: any): boolean {
  return editor.value?.isActive(name, attrs) || false
}

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<template>
  <div class="border rounded-md overflow-hidden">
    <!-- Toolbar -->
    <div class="flex items-center gap-0.5 px-2 py-1 border-b bg-muted/30 flex-wrap">
      <button
        @click="toggleBold"
        :class="isActive('bold') ? 'bg-accent text-foreground' : 'text-muted-foreground'"
        class="h-7 w-7 flex items-center justify-center rounded text-sm font-bold hover:bg-accent"
        title="굵게"
      >B</button>
      <button
        @click="toggleItalic"
        :class="isActive('italic') ? 'bg-accent text-foreground' : 'text-muted-foreground'"
        class="h-7 w-7 flex items-center justify-center rounded text-sm italic hover:bg-accent"
        title="기울임"
      >I</button>
      <button
        @click="toggleUnderline"
        :class="isActive('underline') ? 'bg-accent text-foreground' : 'text-muted-foreground'"
        class="h-7 w-7 flex items-center justify-center rounded text-sm underline hover:bg-accent"
        title="밑줄"
      >U</button>
      <button
        @click="toggleStrike"
        :class="isActive('strike') ? 'bg-accent text-foreground' : 'text-muted-foreground'"
        class="h-7 w-7 flex items-center justify-center rounded text-sm line-through hover:bg-accent"
        title="취소선"
      >S</button>

      <div class="w-px h-5 bg-border mx-1" />

      <button
        @click="toggleH1"
        :class="isActive('heading', { level: 1 }) ? 'bg-accent text-foreground' : 'text-muted-foreground'"
        class="h-7 px-1.5 flex items-center justify-center rounded text-xs font-bold hover:bg-accent"
        title="제목 1"
      >H1</button>
      <button
        @click="toggleH2"
        :class="isActive('heading', { level: 2 }) ? 'bg-accent text-foreground' : 'text-muted-foreground'"
        class="h-7 px-1.5 flex items-center justify-center rounded text-xs font-bold hover:bg-accent"
        title="제목 2"
      >H2</button>

      <div class="w-px h-5 bg-border mx-1" />

      <button
        @click="toggleBulletList"
        :class="isActive('bulletList') ? 'bg-accent text-foreground' : 'text-muted-foreground'"
        class="h-7 w-7 flex items-center justify-center rounded hover:bg-accent"
        title="글머리 기호"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
          <line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" /><line x1="8" y1="18" x2="21" y2="18" />
          <circle cx="4" cy="6" r="1" fill="currentColor" /><circle cx="4" cy="12" r="1" fill="currentColor" /><circle cx="4" cy="18" r="1" fill="currentColor" />
        </svg>
      </button>
      <button
        @click="toggleOrderedList"
        :class="isActive('orderedList') ? 'bg-accent text-foreground' : 'text-muted-foreground'"
        class="h-7 w-7 flex items-center justify-center rounded hover:bg-accent"
        title="번호 매기기"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
          <line x1="10" y1="6" x2="21" y2="6" /><line x1="10" y1="12" x2="21" y2="12" /><line x1="10" y1="18" x2="21" y2="18" />
          <text x="2" y="8" font-size="7" fill="currentColor" stroke="none">1</text>
          <text x="2" y="14" font-size="7" fill="currentColor" stroke="none">2</text>
          <text x="2" y="20" font-size="7" fill="currentColor" stroke="none">3</text>
        </svg>
      </button>

      <div class="w-px h-5 bg-border mx-1" />

      <button
        @click="setLink"
        :class="isActive('link') ? 'bg-accent text-foreground' : 'text-muted-foreground'"
        class="h-7 w-7 flex items-center justify-center rounded hover:bg-accent"
        title="링크"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="h-4 w-4">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
        </svg>
      </button>
      <button
        @click="toggleBlockquote"
        :class="isActive('blockquote') ? 'bg-accent text-foreground' : 'text-muted-foreground'"
        class="h-7 w-7 flex items-center justify-center rounded hover:bg-accent"
        title="인용"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="h-4 w-4">
          <path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V21z" />
          <path d="M15 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V21z" />
        </svg>
      </button>
      <button
        @click="toggleCode"
        :class="isActive('codeBlock') ? 'bg-accent text-foreground' : 'text-muted-foreground'"
        class="h-7 w-7 flex items-center justify-center rounded hover:bg-accent"
        title="코드"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="h-4 w-4">
          <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
        </svg>
      </button>
    </div>

    <!-- Editor content -->
    <EditorContent
      :editor="editor"
      class="prose prose-sm dark:prose-invert max-w-none px-3 py-2 min-h-[12rem] max-h-[24rem] overflow-auto focus-within:outline-none [&_.ProseMirror]:outline-none [&_.ProseMirror]:min-h-[10rem]"
    />
  </div>
</template>
