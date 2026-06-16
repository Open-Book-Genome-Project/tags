# content_formats

**Definition:** The physical or structural form of the work — the "vessel" that contains the content, independent of what that content is about.

---

## What is a Content Format?

Content format answers: **what is the physical or structural shape of this text?**

It is entirely independent of genre, mood, and subject matter. A Graphic Novel can be Horror or Romance. An Anthology can be Fiction or Nonfiction. A Diary can be Memoir or a novel written in diary form.

---

## Core Rules

**The 10-Foot Test:** If you can identify the format from across the room by the visual shape and layout of the text — the way it's typeset, organized, or structured on the page — it is a format.

**Do use content_formats to capture:**
- The structural container or physical form of the work
- Layout-based distinctions (a Script is formatted as Name: Dialogue, regardless of content)
- Length-based distinctions (Novel vs. Novella vs. Short Story, distinguished by word count)

**Do NOT put in content_formats:**
- Genre or narrative mode (that's `genres`)
- Whether the work is fiction or nonfiction (that's `literary_form`)
- The subject of the work

**The Layout-Over-Content Rule:** If the format can be identified purely from how the page looks, without reading the content, it belongs here.

**The Length Rule:** Novel, Novella, and Short Story are distinguished by approximate word count (not plot complexity):
- Short Story: typically under 7,500 words
- Novella: typically 17,500–40,000 words
- Novel: typically 40,000+ words

---

## Edge Cases

| Case | Classification | Reasoning |
|---|---|---|
| Graphic Memoir | Memoir (literary_form=Nonfiction) + Graphic Novel (content_formats) | Format and form are separate |
| Fan Fiction | Novel or Short Story, depending on length | Fandom status is not a format unless structural markers are retained |
| Podcast transcript | Script | Layout is script-like |
| Illustrated chapter book | Novel | Illustrations don't change the prose structure |

---

## Proposing a New Format

See [CONTRIBUTING.md](../CONTRIBUTING.md). A new format must:

1. Be identifiable by structural or visual layout, independent of content
2. Not already be covered by an existing format term
3. Represent a meaningfully distinct structural form

---

## Controlled Vocabulary

See [vocabulary.md](./vocabulary.md).
