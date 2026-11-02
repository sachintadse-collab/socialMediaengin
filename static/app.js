/**
 * Reel Creator Agent — Interactive Mobile-First PWA Controller
 */

let sessionId = localStorage.getItem("reel_session_id") || null;
let currentAudioPreview = null;
let currentPreviewTrackId = null;
let mediaRecorder = null;
let recordedAudioChunks = [];
let recordingTimer = null;
let recordingSeconds = 0;

// Register PWA Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then(reg => console.log('PWA ServiceWorker registered with scope:', reg.scope))
      .catch(err => console.log('PWA ServiceWorker registration failed:', err));
  });
}

// Elements
const chatViewport = document.getElementById("chat-viewport");
const chatInput = document.getElementById("chat-input");
const btnSend = document.getElementById("btn-send");
const btnAttach = document.getElementById("btn-attach");
const globalFileInput = document.getElementById("global-file-input");
const btnRestart = document.getElementById("btn-restart");
const voModal = document.getElementById("vo-modal");
const voVideo = document.getElementById("vo-video");
const btnVoAction = document.getElementById("btn-vo-action");
const voStatusText = document.getElementById("vo-status-text");
const sessionBadge = document.getElementById("session-badge");

// Initialize application
async function initApp() {
  try {
    const res = await fetch(`/api/session${sessionId ? `?session_id=${sessionId}` : ''}`);
    const data = await res.json();
    sessionId = data.session_id;
    localStorage.setItem("reel_session_id", sessionId);
    sessionBadge.textContent = `ID: ${sessionId}`;

    // Send initial greeting trigger
    sendMessage("", {});
  } catch (err) {
    console.error("Init failed:", err);
  }
}

// Global direct file upload handler
async function uploadFilesDirectly(files) {
  if (!files || files.length === 0) return;
  appendMessage("user", `📁 Uploading ${files.length} file(s): ${files.map(f => f.name).join(", ")}`);
  
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("type", "media");
  files.forEach(f => formData.append("files", f));

  try {
    const res = await fetch("/api/upload", { method: "POST", body: formData });
    const data = await res.json();
    sendMessage("Media files uploaded, please analyze.", {});
  } catch (err) {
    appendMessage("agent", "❌ Upload failed. Please check network connection and try again.");
  }
}

// Send user message or interactive card payload
async function sendMessage(text = "", payload = {}) {
  if (text.trim()) {
    appendMessage("user", text);
  }
  chatInput.value = "";
  btnSend.disabled = true;

  try {
    const res = await fetch("/api/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        message: text,
        payload: payload
      })
    });
    const data = await res.json();
    handleAgentResponse(data);
  } catch (err) {
    appendMessage("agent", "⚠️ Connection error. Please try again.");
  } finally {
    btnSend.disabled = false;
  }
}

// Render agent message & interactive components
function handleAgentResponse(data) {
  if (data.text) {
    appendMessage("agent", data.text, data);
  }
}

function appendMessage(sender, text, meta = null) {
  const row = document.createElement("div");
  row.className = `message-row ${sender}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = sender === "agent" ? "✨" : "👤";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.innerHTML = formatMarkdown(text);

  // Append media previews carousel if present
  if (meta && meta.media_previews && meta.media_previews.length > 0) {
    const gallery = document.createElement("div");
    gallery.className = "media-gallery-tray";
    meta.media_previews.forEach(m => {
      const item = document.createElement("div");
      item.className = "gallery-item";
      item.innerHTML = `
        <img src="${m.thumbnail_url}" alt="${m.file_name}" class="gallery-thumb" onerror="this.src='/static/icons/icon-192.png'" />
        <span class="gallery-fname" title="${m.file_name}">${m.file_name}</span>
      `;
      gallery.appendChild(item);
    });
    bubble.appendChild(gallery);
  }

  // Append interactive widget if present
  if (meta && meta.interactive_type) {
    const widget = createInteractiveWidget(meta);
    if (widget) bubble.appendChild(widget);
  }

  // Append video player if reel url is present
  if (meta && meta.reel_url) {
    const playerContainer = document.createElement("div");
    playerContainer.className = "reel-player-container";
    const video = document.createElement("video");
    video.className = "reel-video";
    video.src = meta.reel_url;
    video.controls = true;
    video.playsInline = true;
    playerContainer.appendChild(video);
    bubble.appendChild(playerContainer);
  }

  row.appendChild(avatar);
  row.appendChild(bubble);
  chatViewport.appendChild(row);
  chatViewport.scrollTop = chatViewport.scrollHeight;
}

// Simple markdown formatter
function formatMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code style="background:rgba(255,255,255,0.1);padding:2px 6px;border-radius:4px;">$1</code>')
    .replace(/\n/g, '<br/>');
}

// Create interactive card widgets based on agent state
function createInteractiveWidget(meta) {
  const card = document.createElement("div");
  card.className = "interactive-card";

  // 1. File Upload Dropzone
  if (meta.interactive_type === "file_upload") {
    card.innerHTML = `
      <div class="dropzone" id="media-dropzone">
        <div class="dropzone-icon">📁</div>
        <strong>Tap or Drop Media Files Here</strong>
        <p style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Supports Images (.jpg, .png), Videos (.mp4, .mov), and Audio</p>
        <input type="file" id="media-file-input" multiple accept="image/*,video/*,audio/*" style="display: none;" />
      </div>
      <div class="file-preview-tray" id="file-tray"></div>
      <button class="btn-primary" id="btn-upload-confirm" style="display: none;">Upload & Analyze Vibe</button>
    `;

    setTimeout(() => {
      const dropzone = card.querySelector("#media-dropzone");
      const fileInput = card.querySelector("#media-file-input");
      const tray = card.querySelector("#file-tray");
      const btnConfirm = card.querySelector("#btn-upload-confirm");
      let selectedFiles = [];

      dropzone.onclick = () => fileInput.click();
      fileInput.onchange = (e) => handleFiles(Array.from(e.target.files));

      dropzone.ondragover = (e) => { e.preventDefault(); dropzone.classList.add("active"); };
      dropzone.ondragleave = () => dropzone.classList.remove("active");
      dropzone.ondrop = (e) => {
        e.preventDefault();
        dropzone.classList.remove("active");
        handleFiles(Array.from(e.dataTransfer.files));
      };

      function handleFiles(files) {
        selectedFiles = files;
        tray.innerHTML = "";
        files.forEach(f => {
          const item = document.createElement("div");
          item.style.fontSize = "11px";
          item.style.padding = "4px 8px";
          item.style.background = "var(--bg-card)";
          item.style.borderRadius = "4px";
          item.textContent = f.name;
          tray.appendChild(item);
        });
        if (files.length > 0) {
          btnConfirm.style.display = "block";
          btnConfirm.textContent = `Upload ${files.length} Asset(s) & Continue`;
        }
      }

      btnConfirm.onclick = async () => {
        btnConfirm.disabled = true;
        btnConfirm.textContent = "Uploading & Inspecting...";
        const formData = new FormData();
        formData.append("session_id", sessionId);
        formData.append("type", "media");
        selectedFiles.forEach(f => formData.append("files", f));

        const res = await fetch("/api/upload", { method: "POST", body: formData });
        const resData = await res.json();
        btnConfirm.remove();
        dropzone.remove();
        sendMessage("Media files uploaded, please analyze.", {});
      };
    }, 50);

    return card;
  }

  // 2. Confirm Vibe Options
  if (meta.interactive_type === "confirm_vibe" && meta.options) {
    const grid = document.createElement("div");
    grid.className = "options-grid";
    meta.options.forEach(opt => {
      const btn = document.createElement("button");
      btn.className = "btn-option";
      btn.textContent = opt;
      btn.onclick = () => {
        card.remove();
        sendMessage(opt, { custom_vibe: opt.replace(/^✅ Yes, proceed with '|'$/g, '') });
      };
      grid.appendChild(btn);
    });
    card.appendChild(grid);
    return card;
  }

  // 3. Select BGM (All Library Tracks)
  if (meta.interactive_type === "select_bgm" && meta.tracks) {
    const wrapper = document.createElement("div");
    
    wrapper.innerHTML = `
      <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px; font-weight: 500; display: flex; justify-content: space-between; align-items: center;">
        <span>🎧 Audio Library (${meta.tracks.length} tracks available):</span>
        <span style="font-size: 10px; color: var(--accent); font-weight: 600;">Auto-trims to reel duration</span>
      </div>
      <div class="bgm-library-scroll" style="max-height: 380px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding-right: 4px; margin-bottom: 8px;">
      </div>
    `;

    const container = wrapper.querySelector(".bgm-library-scroll");

    meta.tracks.forEach(track => {
      const row = document.createElement("div");
      row.className = "track-card";
      const isTopMatch = track._score && track._score > 0;
      if (isTopMatch) {
        row.style.borderColor = "rgba(138, 92, 246, 0.4)";
      }

      row.innerHTML = `
        <div class="track-info" style="flex: 1; min-width: 0;">
          <div class="track-title" style="display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600;">
            <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${track.title}</span>
            ${isTopMatch ? `<span style="font-size: 9px; background: rgba(138, 92, 246, 0.3); border: 1px solid var(--accent); color: #fff; padding: 2px 6px; border-radius: 8px; font-weight: 600; white-space: nowrap; flex-shrink: 0;">✨ Vibe Match</span>` : ''}
          </div>
          <div class="track-vibe" style="font-size: 11px; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            ${track.bpm} • ${track.vibe}
          </div>
        </div>
        <div class="track-actions" style="display: flex; gap: 8px; align-items: center; flex-shrink: 0;">
          <button class="btn-icon" data-url="${track.preview_url}" title="Preview Audio" style="width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0;">▶</button>
          <button class="btn-select-track" data-id="${track.id}" style="padding: 7px 14px; font-size: 12px; font-weight: 600; white-space: nowrap; flex-shrink: 0; min-width: 65px; border-radius: 8px; cursor: pointer;">Select</button>
        </div>
      `;

      const btnPlay = row.querySelector(".btn-icon");
      const btnSelect = row.querySelector(".btn-select-track");

      btnPlay.onclick = () => toggleAudioPreview(track.preview_url, btnPlay);
      btnSelect.onclick = () => {
        stopAudioPreview();
        card.remove();
        sendMessage(`Selected ${track.title}`, { track_id: track.id });
      };

    container.appendChild(row);
    });

    // Option to proceed without BGM (FR-04.3)
    const btnNoBgm = document.createElement("button");
    btnNoBgm.className = "btn-option";
    btnNoBgm.style.width = "100%";
    btnNoBgm.style.padding = "9px 12px";
    btnNoBgm.style.fontSize = "12px";
    btnNoBgm.style.marginTop = "6px";
    btnNoBgm.innerHTML = "🔇 Proceed without BGM (Silent Reel)";
    btnNoBgm.onclick = () => {
      stopAudioPreview();
      card.remove();
      sendMessage("Proceed without BGM (Silent)", { mute_audio: true });
    };
    wrapper.appendChild(btnNoBgm);

    card.appendChild(wrapper);
    return card;
  }

  // 4. Edit Scene Descriptions (With Thumbnails & Description at Bottom of Media)
  if (meta.interactive_type === "edit_scene_descriptions" && meta.scenes) {
    const inputs = [];
    meta.scenes.forEach(s => {
      const cardItem = document.createElement("div");
      cardItem.className = "scene-item-card";
      cardItem.innerHTML = `
        <div class="scene-media-header">
          <img src="${s.thumbnail_url}" alt="${s.file_name}" class="scene-thumb-preview" onerror="this.src='/static/icons/icon-192.png'" />
          <div class="scene-meta-info">
            <span class="scene-number-pill">Scene ${s.index + 1}</span>
            <span class="scene-filename">${s.file_name}</span>
            ${s.theme_badge ? `<span class="scene-tag-badge">${s.theme_badge}</span>` : ''}
          </div>
        </div>
        <div class="scene-desc-footer">
          <label class="scene-desc-label">Description (Editable at bottom):</label>
          <textarea class="chat-input scene-textarea" rows="2">${s.description}</textarea>
        </div>
      `;
      const textareaEl = cardItem.querySelector("textarea");
      inputs.push(textareaEl);
      card.appendChild(cardItem);
    });

    const btnConfirm = document.createElement("button");
    btnConfirm.className = "btn-primary";
    btnConfirm.textContent = "✅ Approve Descriptions & Continue";
    btnConfirm.onclick = () => {
      const descriptions = inputs.map(i => i.value.trim());
      card.remove();
      sendMessage("Descriptions approved.", { scene_descriptions: descriptions });
    };
    card.appendChild(btnConfirm);
    return card;
  }

  // 5. Edit Reel Caption & Regeneration Options
  if (meta.interactive_type === "edit_reel_caption") {
    let options = (meta.caption_options && meta.caption_options.length > 0) ? meta.caption_options : [
      {
        style: "🥻 Poetic Heritage",
        caption: meta.caption || "Six yards of pure elegance, timeless heritage, and artisan grace 🥻✨ Every thread weaves a story of tradition that never goes out of style. Which drape is your favorite? Let us know in the comments! 👇\n\n#sareelove #handloomsaree #silksaree #ethnicwear #indianfashion #sareedraping #traditionalwear #festivecollection #ootd"
      },
      {
        style: "🛍️ Boutique & Shop",
        caption: "Festive Collection Drop 🥻✨ Handcrafted with exquisite zari borders and lustrous silk textures. Perfect for weddings, celebrations, and festive gatherings. Limited pieces available—DM us to order or tap link in bio! 🛍️👇\n\n#festivewear #handloomsaree #silksarees #boutiquefashion #indianwedding #ethniccollection #shopnow"
      },
      {
        style: "⚡ Short & Aesthetic",
        caption: "Draped in timeless grace 💫 Pure artisan handloom in every fold. 🥻✨\n\n#sareelove #traditionalwear #handloom #ethnicfashion #aestheticreels #indiancouture"
      },
      {
        style: "🔥 Viral Engagement",
        caption: "Rate this drape from 1 to 10 in the comments! 👇 Would you wear this to an upcoming celebration? Save this reel for your festive wardrobe inspiration! ✨🥻\n\n#sareeinspiration #ethnicdrape #fashionpoll #handloomlove #festiveseason #trendingreels"
      }
    ];

    let currentIdx = 0;

    function buildChipsHtml(opts, activeIndex = 0) {
      return `
        <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 6px; font-weight: 500; display: flex; justify-content: space-between; align-items: center;">
          <span>💡 Select a caption style:</span>
          <span style="font-size: 10px; color: var(--accent); font-weight: 600;">${opts.length} styles available</span>
        </div>
        <div class="caption-style-chips-container" style="display: flex; gap: 6px; overflow-x: auto; padding-bottom: 6px; margin-bottom: 6px;">
          ${opts.map((opt, i) => `
            <button type="button" class="btn-caption-style" data-index="${i}" style="
              background: ${i === activeIndex ? 'linear-gradient(135deg, rgba(138, 92, 246, 0.4), rgba(236, 72, 153, 0.4))' : 'rgba(255, 255, 255, 0.07)'};
              border: 1px solid ${i === activeIndex ? 'var(--accent)' : 'rgba(255, 255, 255, 0.15)'};
              color: ${i === activeIndex ? '#ffffff' : 'var(--text-main)'};
              padding: 6px 12px;
              border-radius: 14px;
              font-size: 11px;
              font-weight: ${i === activeIndex ? '600' : '500'};
              white-space: nowrap;
              cursor: pointer;
              transition: all 0.2s ease;
            ">
              ${opt.style}
            </button>
          `).join('')}
        </div>
      `;
    }

    card.innerHTML = `
      <div id="caption-chips-wrapper">
        ${buildChipsHtml(options, currentIdx)}
      </div>
      <textarea id="caption-input" class="chat-input" style="width: 100%; min-height: 140px; height: 150px; border-radius: 8px; font-size: 13px; line-height: 1.4; resize: vertical;">${meta.caption || options[0].caption}</textarea>
      <div id="caption-status-hint" style="font-size: 11px; color: var(--accent); margin-top: 4px; min-height: 16px; font-weight: 500;"></div>
      <div style="display: flex; gap: 8px; margin-top: 8px;">
        <button class="btn-option" id="btn-regenerate-caption" style="flex: 1; padding: 10px; display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 12px; font-weight: 600;" type="button">
          🔄 Regenerate
        </button>
        <button class="btn-primary" id="btn-confirm-caption" style="flex: 1.6; padding: 10px; font-size: 13px; font-weight: 600;" type="button">
          ✅ Approve Caption
        </button>
      </div>
    `;

    setTimeout(() => {
      const btnApprove = card.querySelector("#btn-confirm-caption");
      const btnRegen = card.querySelector("#btn-regenerate-caption");
      const txt = card.querySelector("#caption-input");
      const hint = card.querySelector("#caption-status-hint");

      function attachChipListeners() {
        const chips = card.querySelectorAll(".btn-caption-style");
        chips.forEach(chip => {
          chip.onclick = () => {
            const idx = parseInt(chip.dataset.index, 10);
            applyStyle(idx);
          };
        });
      }

      function applyStyle(idx) {
        if (!options[idx]) return;
        currentIdx = idx;
        txt.value = options[idx].caption;
        txt.scrollTop = 0;
        const chips = card.querySelectorAll(".btn-caption-style");
        chips.forEach((c, i) => {
          if (i === idx) {
            c.style.background = "linear-gradient(135deg, rgba(138, 92, 246, 0.4), rgba(236, 72, 153, 0.4))";
            c.style.borderColor = "var(--accent)";
            c.style.color = "#ffffff";
            c.style.fontWeight = "600";
          } else {
            c.style.background = "rgba(255, 255, 255, 0.07)";
            c.style.borderColor = "rgba(255, 255, 255, 0.15)";
            c.style.color = "var(--text-main)";
            c.style.fontWeight = "500";
          }
        });
        if (hint) {
          hint.textContent = `✨ Swapped to "${options[idx].style}" style`;
          setTimeout(() => { if (hint && hint.textContent.includes(options[idx].style)) hint.textContent = ""; }, 2500);
        }
      }

      attachChipListeners();

      // Regenerate button: updates in-place WITHOUT removing card or advancing state!
      if (btnRegen) {
        btnRegen.onclick = async () => {
          btnRegen.disabled = true;
          const origHtml = btnRegen.innerHTML;
          btnRegen.innerHTML = `⏳ Loading...`;

          try {
            const res = await fetch(`/api/caption_options?session_id=${encodeURIComponent(sessionId)}`);
            if (res.ok) {
              const data = await res.json();
              if (data.options && data.options.length > 0) {
                options = data.options;
                const wrapper = card.querySelector("#caption-chips-wrapper");
                if (wrapper) {
                  wrapper.innerHTML = buildChipsHtml(options, 0);
                  attachChipListeners();
                }
                applyStyle(0);
                if (hint) {
                  hint.textContent = `✨ Fresh caption variations generated!`;
                  setTimeout(() => { if (hint) hint.textContent = ""; }, 3000);
                }
                btnRegen.innerHTML = origHtml;
                btnRegen.disabled = false;
                return;
              }
            }
          } catch (err) {
            console.warn("Could not fetch remote caption options, cycling locally:", err);
          }

          // In-place local cycle fallback
          currentIdx = (currentIdx + 1) % options.length;
          applyStyle(currentIdx);
          btnRegen.innerHTML = origHtml;
          btnRegen.disabled = false;
        };
      }

      // Approve button: ONLY this advances to hook selection!
      if (btnApprove) {
        btnApprove.onclick = () => {
          const approvedCaption = txt.value.trim();
          card.remove();
          sendMessage("Caption approved.", { action: "approve_caption", reel_caption: approvedCaption });
        };
      }
    }, 50);

    return card;
  }

  // 6. Select Hook & Regeneration Options
  if (meta.interactive_type === "select_hook" && meta.hooks) {
    let hooks = meta.hooks;

    function buildHookButtons(hookList) {
      return hookList.map(hook => `
        <button class="btn-option btn-hook-option" style="
          width: 100%;
          text-align: left;
          padding: 12px 14px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 8px;
          border-radius: 10px;
          border: 1px solid rgba(255, 255, 255, 0.12);
          background: rgba(255, 255, 255, 0.04);
          transition: all 0.2s ease;
          cursor: pointer;
        " data-hook="${encodeURIComponent(hook)}">
          <span style="flex: 1; font-size: 13px; line-height: 1.4; color: var(--text-main); font-weight: 500;">
            "${hook}"
          </span>
          <span style="
            background: linear-gradient(135deg, rgba(138, 92, 246, 0.25), rgba(236, 72, 153, 0.25));
            border: 1px solid var(--accent);
            color: #ffffff;
            padding: 5px 12px;
            border-radius: 14px;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
            flex-shrink: 0;
            margin-left: 6px;
          ">
            Select →
          </span>
        </button>
      `).join('');
    }

    card.innerHTML = `
      <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px; font-weight: 500; display: flex; justify-content: space-between; align-items: center;">
        <span>💡 Tap any hook to select it, or write your own:</span>
        <span id="hook-count-indicator" style="font-size: 10px; color: var(--accent); font-weight: 600;">${hooks.length} options</span>
      </div>
      <div id="hook-list-container">
        ${buildHookButtons(hooks)}
      </div>

      <!-- Custom Hook Input -->
      <div style="display: flex; gap: 8px; margin-top: 10px;">
        <input type="text" id="custom-hook-input" class="chat-input" placeholder="Or write custom hook text..." style="flex: 1; font-size: 13px; padding: 10px 12px; border-radius: 8px;">
        <button type="button" id="btn-use-custom-hook" class="btn-primary" style="padding: 10px 14px; font-size: 12px; font-weight: 600; white-space: nowrap;">
          Use Custom
        </button>
      </div>

      <!-- Regenerate Action Row -->
      <div style="display: flex; gap: 8px; margin-top: 8px;">
        <button type="button" id="btn-regenerate-hooks" class="btn-option" style="flex: 1; padding: 10px; display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 12px; font-weight: 600;">
          🔄 Regenerate Hooks
        </button>
      </div>
      <div id="hook-status-hint" style="font-size: 11px; color: var(--accent); margin-top: 4px; min-height: 16px; font-weight: 500; text-align: center;"></div>
    `;

    setTimeout(() => {
      const container = card.querySelector("#hook-list-container");
      const btnRegen = card.querySelector("#btn-regenerate-hooks");
      const btnCustom = card.querySelector("#btn-use-custom-hook");
      const customInput = card.querySelector("#custom-hook-input");
      const hint = card.querySelector("#hook-status-hint");

      function attachHookListeners() {
        const buttons = container.querySelectorAll(".btn-hook-option");
        buttons.forEach(btn => {
          btn.onclick = () => {
            const hook = decodeURIComponent(btn.dataset.hook);
            card.remove();
            sendMessage(hook, { hook_text: hook });
          };
        });
      }

      attachHookListeners();

      // Custom Hook selection
      if (btnCustom && customInput) {
        btnCustom.onclick = () => {
          const customText = customInput.value.trim();
          if (customText) {
            card.remove();
            sendMessage(customText, { hook_text: customText });
          } else {
            customInput.focus();
          }
        };

        customInput.onkeydown = (e) => {
          if (e.key === "Enter") {
            btnCustom.click();
          }
        };
      }

      // Regenerate Hooks button: updates in-place WITHOUT removing card or advancing state!
      if (btnRegen) {
        btnRegen.onclick = async () => {
          btnRegen.disabled = true;
          const origHtml = btnRegen.innerHTML;
          btnRegen.innerHTML = `⏳ Loading fresh hooks...`;

          try {
            const res = await fetch(`/api/hook_options?session_id=${encodeURIComponent(sessionId)}`);
            if (res.ok) {
              const data = await res.json();
              if (data.hooks && data.hooks.length > 0) {
                hooks = data.hooks;
                container.innerHTML = buildHookButtons(hooks);
                attachHookListeners();
                if (hint) {
                  hint.textContent = `✨ 4 new viral hooks loaded!`;
                  setTimeout(() => { if (hint) hint.textContent = ""; }, 3000);
                }
                btnRegen.innerHTML = origHtml;
                btnRegen.disabled = false;
                return;
              }
            }
          } catch (err) {
            console.warn("Could not fetch remote hooks, cycling locally:", err);
          }

          // Fallback: cycle in-place
          hooks = hooks.slice(1).concat(hooks.slice(0, 1));
          container.innerHTML = buildHookButtons(hooks);
          attachHookListeners();
          btnRegen.innerHTML = origHtml;
          btnRegen.disabled = false;
        };
      }
    }, 50);

    return card;
  }

  // 7. Branding Inquiry
  if (meta.interactive_type === "branding_inquiry") {
    const grid = document.createElement("div");
    grid.className = "options-grid";
    meta.options.forEach(opt => {
      const btn = document.createElement("button");
      btn.className = "btn-option";
      btn.textContent = opt;
      btn.onclick = () => {
        card.remove();
        const hasBrand = opt.includes("Yes");
        sendMessage(opt, { has_branding: hasBrand });
      };
      grid.appendChild(btn);
    });
    card.appendChild(grid);
    return card;
  }

  // 8. Branding Logo & Position
  if (meta.interactive_type === "branding_upload_and_position") {
    card.innerHTML = `
      <div style="font-size: 12px; font-weight: bold; margin-bottom: 4px;">1. Upload Brand Logo (PNG)</div>
      <input type="file" id="logo-input" accept="image/png,image/jpeg,image/webp" style="margin-bottom: 12px; font-size: 12px;" />
      
      <div style="font-size: 12px; font-weight: bold; margin-bottom: 4px;">2. Select Logo Placement:</div>
      <div class="branding-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px;">
        <button class="btn-pos" data-pos="Top-Left">Top-Left</button>
        <button class="btn-pos selected" data-pos="Top-Right">Top-Right</button>
        <button class="btn-pos" data-pos="Center">Center</button>
        <button class="btn-pos" data-pos="Bottom-Left">Bottom-Left</button>
        <button class="btn-pos" data-pos="Bottom-Right">Bottom-Right</button>
        <button class="btn-pos" data-pos="Background">Background</button>
      </div>
      <button class="btn-primary" id="btn-save-branding" style="margin-top: 12px;">Confirm & Assemble Reel</button>
    `;

    setTimeout(() => {
      let selectedPosition = "Top-Right";
      const posButtons = card.querySelectorAll(".btn-pos");
      posButtons.forEach(btn => {
        btn.onclick = () => {
          posButtons.forEach(b => b.classList.remove("selected"));
          btn.classList.add("selected");
          selectedPosition = btn.dataset.pos;
        };
      });

      const btnSave = card.querySelector("#btn-save-branding");
      const logoInput = card.querySelector("#logo-input");

      logoInput.onchange = (e) => {
        if (e.target.files && e.target.files[0]) {
          const reader = new FileReader();
          reader.onload = (ev) => {
            let logoPrev = card.querySelector("#logo-thumb-preview");
            if (!logoPrev) {
              logoPrev = document.createElement("img");
              logoPrev.id = "logo-thumb-preview";
              logoPrev.style = "max-height: 60px; max-width: 120px; object-fit: contain; margin-bottom: 10px; border: 1px solid var(--border-color); padding: 4px; border-radius: 6px; background: rgba(255,255,255,0.06); display: block;";
              logoInput.parentNode.insertBefore(logoPrev, logoInput.nextSibling);
            }
            logoPrev.src = ev.target.result;
          };
          reader.readAsDataURL(e.target.files[0]);
        }
      };

      btnSave.onclick = async () => {
        btnSave.disabled = true;
        btnSave.textContent = "Uploading & Assembling...";

        if (logoInput.files.length > 0) {
          const formData = new FormData();
          formData.append("session_id", sessionId);
          formData.append("type", "branding");
          formData.append("file", logoInput.files[0]);
          await fetch("/api/upload", { method: "POST", body: formData });
        }

        card.remove();
        sendMessage(`Branding position: ${selectedPosition}`, { position: selectedPosition });
      };
    }, 50);

    return card;
  }

  // 9. Voiceover Inquiry
  if (meta.interactive_type === "voiceover_inquiry" && meta.options) {
    const grid = document.createElement("div");
    grid.className = "options-grid";
    meta.options.forEach(opt => {
      const btn = document.createElement("button");
      btn.className = "btn-option";
      btn.textContent = opt;
      btn.onclick = () => {
        card.remove();
        const wantsVO = opt.includes("Yes");
        sendMessage(opt, { wants_voiceover: wantsVO });
      };
      grid.appendChild(btn);
    });
    card.appendChild(grid);
    return card;
  }

  // 10. Record Voiceover Trigger
  if (meta.interactive_type === "record_voiceover") {
    const btnRecord = document.createElement("button");
    btnRecord.className = "btn-primary";
    btnRecord.style.background = "linear-gradient(135deg, var(--danger-color), #ff4757)";
    btnRecord.textContent = "🎙️ Open Voiceover Studio";
    btnRecord.onclick = () => openVoiceoverStudio(meta.reel_url);
    card.appendChild(btnRecord);
    return card;
  }

  // 11. Final Download Card
  if (meta.interactive_type === "download_final") {
    card.innerHTML = `
      <a href="${meta.download_url}" download="reel_final.mp4" class="btn-primary" style="display: block; text-align: center; font-size: 15px; padding: 14px;">
        ⬇️ Download Ready Reel (MP4)
      </a>
      <div style="font-size: 11px; color: var(--text-muted); text-align: center; margin-top: 6px;">1080x1920 • 9:16 Vertical • High Bitrate</div>
    `;
    return card;
  }

  return null;
}

// BGM Audio Preview helpers
function toggleAudioPreview(url, btnElement) {
  if (currentAudioPreview && currentPreviewTrackId === url) {
    if (currentAudioPreview.paused) {
      currentAudioPreview.play().catch(e => console.warn("Audio play failed:", e));
      btnElement.textContent = "⏸";
    } else {
      currentAudioPreview.pause();
      btnElement.textContent = "▶";
    }
  } else {
    stopAudioPreview();
    currentAudioPreview = new Audio(url);
    currentPreviewTrackId = url;
    currentAudioPreview.play().catch(e => {
      console.warn("Audio preview failed:", e);
      btnElement.textContent = "▶";
    });
    btnElement.textContent = "⏸";
    currentAudioPreview.onended = () => {
      btnElement.textContent = "▶";
    };
    currentAudioPreview.onerror = () => {
      btnElement.textContent = "▶";
    };
  }
}

function stopAudioPreview() {
  if (currentAudioPreview) {
    currentAudioPreview.pause();
    currentAudioPreview = null;
    currentPreviewTrackId = null;
    document.querySelectorAll(".track-card .btn-icon").forEach(b => b.textContent = "▶");
  }
}

// Synchronized Voiceover Studio (Requirement 11)
function openVoiceoverStudio(reelUrl) {
  voVideo.src = reelUrl;
  voModal.classList.add("active");
  voStatusText.textContent = "Ready to record";
  btnVoAction.textContent = "🎙️ Start Synchronized Recording";
  btnVoAction.style.background = "linear-gradient(135deg, var(--danger-color), #ff4757)";
  recordedAudioChunks = [];

  btnVoAction.onclick = async () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      stopRecordingVoiceover();
    } else {
      startRecordingVoiceover();
    }
  };
}

async function startRecordingVoiceover() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    recordedAudioChunks = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) recordedAudioChunks.push(e.data);
    };

    mediaRecorder.onstop = uploadRecordedVoiceover;

    // Reset video to start and mute it so mic doesn't catch BGM
    voVideo.currentTime = 0;
    voVideo.muted = true;
    voVideo.play();
    mediaRecorder.start();

    btnVoAction.textContent = "⏹️ Stop Recording";
    voStatusText.innerHTML = `<span class="rec-dot"></span> Recording in sync...`;

    // Stop automatically when video ends
    voVideo.onended = () => {
      if (mediaRecorder && mediaRecorder.state === "recording") {
        stopRecordingVoiceover();
      }
    };
  } catch (err) {
    alert("Microphone access is required to record voiceover.");
  }
}

function stopRecordingVoiceover() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    voVideo.pause();
    voStatusText.textContent = "Processing & removing BGM...";
    btnVoAction.disabled = true;
  }
}

async function uploadRecordedVoiceover() {
  const audioBlob = new Blob(recordedAudioChunks, { type: "audio/wav" });
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("audio", audioBlob, "voiceover.wav");

  try {
    const res = await fetch("/api/voiceover", { method: "POST", body: formData });
    const data = await res.json();
    voModal.classList.remove("active");
    btnVoAction.disabled = false;
    handleAgentResponse(data);
  } catch (err) {
    alert("Voiceover upload failed. Please try again.");
    btnVoAction.disabled = false;
  }
}

// Event Listeners
btnSend.onclick = () => {
  const text = chatInput.value.trim();
  if (text) sendMessage(text);
};

chatInput.onkeydown = (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    btnSend.click();
  }
};

// 1. Restart / New Reel Button Listener
if (btnRestart) {
  btnRestart.onclick = async () => {
    localStorage.removeItem("reel_session_id");
    sessionId = null;
    chatViewport.innerHTML = "";
    sessionBadge.textContent = "Connecting...";
    try {
      const res = await fetch("/api/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      const data = await res.json();
      sessionId = data.session.session_id;
      localStorage.setItem("reel_session_id", sessionId);
      sessionBadge.textContent = `ID: ${sessionId}`;
      handleAgentResponse(data);
    } catch (err) {
      console.error("Reset request error:", err);
      window.location.reload();
    }
  };
}

// 2. Attach Media Button Listener
if (btnAttach && globalFileInput) {
  btnAttach.onclick = () => {
    globalFileInput.click();
  };
  globalFileInput.onchange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      uploadFilesDirectly(Array.from(e.target.files));
      e.target.value = "";
    }
  };
}

// 3. Global Drag and Drop support onto chat window
const appContainer = document.querySelector(".app-container");
if (appContainer) {
  appContainer.ondragover = (e) => { e.preventDefault(); };
  appContainer.ondrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      uploadFilesDirectly(Array.from(e.dataTransfer.files));
    }
  };
}

// Start
initApp();

