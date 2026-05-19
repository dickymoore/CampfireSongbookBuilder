---
stateFile: "/home/dicky/CampfireSongbookBuilder/_bmad-output/story-automator/orchestration-1-20260519-165455.md"
createdAt: "2026-05-19T16:55:26Z"
---

# Agents Plan: CampfireSongbookBuilder - Epic Breakdown

```json
{
  "version": "1.0.0",
  "stateFile": "/home/dicky/CampfireSongbookBuilder/_bmad-output/story-automator/orchestration-1-20260519-165455.md",
  "epic": "1",
  "epicName": "CampfireSongbookBuilder - Epic Breakdown",
  "createdAt": "2026-05-19T16:55:26Z",
  "stories": [
    {
      "storyId": "1.1",
      "title": "Define Quality Data Contracts",
      "complexity": "medium",
      "tasks": {
        "create": {
          "primary": "codex",
          "fallback": "claude"
        },
        "dev": {
          "primary": "codex",
          "fallback": "claude"
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "codex",
          "fallback": "claude"
        }
      }
    },
    {
      "storyId": "1.2",
      "title": "Detect Missing or Unusable Lyrics and Chords",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "1.3",
      "title": "Detect Junk, Markup, and Duplicate Content",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "1.4",
      "title": "Detect Print-Hostile and Low-Confidence Content",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "1.5",
      "title": "Persist Current Quality Status for Cached Content",
      "complexity": "medium",
      "tasks": {
        "create": {
          "primary": "codex",
          "fallback": "claude"
        },
        "dev": {
          "primary": "codex",
          "fallback": "claude"
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "codex",
          "fallback": "claude"
        }
      }
    },
    {
      "storyId": "2.1",
      "title": "Record Source Attempts During Fetching",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "2.2",
      "title": "Retry Alternate Sources Before Final Questionable Status",
      "complexity": "medium",
      "tasks": {
        "create": {
          "primary": "codex",
          "fallback": "claude"
        },
        "dev": {
          "primary": "codex",
          "fallback": "claude"
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "codex",
          "fallback": "claude"
        }
      }
    },
    {
      "storyId": "2.3",
      "title": "Persist Review Decisions with Content Hashes",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "2.4",
      "title": "Apply Questionable Exclusion and Override Rules",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "2.5",
      "title": "Produce Traceable Quality Reports",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "3.1",
      "title": "Validate Source List Rows Before Fetching",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "3.2",
      "title": "Summarize Newly Added Song Outcomes",
      "complexity": "medium",
      "tasks": {
        "create": {
          "primary": "codex",
          "fallback": "claude"
        },
        "dev": {
          "primary": "codex",
          "fallback": "claude"
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "codex",
          "fallback": "claude"
        }
      }
    },
    {
      "storyId": "3.3",
      "title": "Keep File and CLI Workflows Agent-Friendly",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "4.1",
      "title": "Load and Validate Favourite Songs",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "4.2",
      "title": "Load and Validate Named Selections",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "4.3",
      "title": "Generate Quality-Filtered Favourite and Selection Books",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "4.4",
      "title": "Report Selection Completeness Before Output",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "5.1",
      "title": "Enforce Network-Free Offline Generation",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "5.2",
      "title": "Preserve Backward-Compatible Cache Reads",
      "complexity": "medium",
      "tasks": {
        "create": {
          "primary": "codex",
          "fallback": "claude"
        },
        "dev": {
          "primary": "codex",
          "fallback": "claude"
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "codex",
          "fallback": "claude"
        }
      }
    },
    {
      "storyId": "5.3",
      "title": "Render Accepted Content to Markdown",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "5.4",
      "title": "Generate `.docx` from Accepted Content",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "5.5",
      "title": "Add Recoverable Optional PDF Conversion",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    },
    {
      "storyId": "5.6",
      "title": "Apply Basic Printable Layout Quality Checks",
      "complexity": "low",
      "tasks": {
        "create": {
          "primary": "claude",
          "fallback": false
        },
        "dev": {
          "primary": "claude",
          "fallback": false
        },
        "auto": {
          "primary": "codex",
          "fallback": false
        },
        "review": {
          "primary": "claude",
          "fallback": false
        }
      }
    }
  ]
}
```
