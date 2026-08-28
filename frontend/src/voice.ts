import "./voice.css";

if (new URLSearchParams(window.location.search).has("embedded")) {
  document.documentElement.classList.add("embedded");
}

type AgentResponse = {
  conversation_id: string;
  reply: string;
  tool: { name: string; result?: { status?: string; video_id?: string; title?: string; watch_url?: string } } | null;
};

type SpeechRecognitionEventLike = Event & {
  results: ArrayLike<{ 0: { transcript: string } }>;
};

type Recognition = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
};

type RecognitionConstructor = new () => Recognition;

declare global {
  interface Window {
    SpeechRecognition?: RecognitionConstructor;
    webkitSpeechRecognition?: RecognitionConstructor;
  }
}

const status = document.querySelector<HTMLParagraphElement>("#status")!;
const listenButton = document.querySelector<HTMLButtonElement>("#listen")!;
const form = document.querySelector<HTMLFormElement>("#message-form")!;
const input = document.querySelector<HTMLInputElement>("#message")!;
const transcript = document.querySelector<HTMLParagraphElement>("#transcript")!;
const reply = document.querySelector<HTMLParagraphElement>("#reply")!;
const speak = document.querySelector<HTMLInputElement>("#speak")!;
const core = document.querySelector<HTMLDivElement>("#core")!;
const voiceName = document.querySelector<HTMLElement>("#voice-name")!;
const sessionTime = document.querySelector<HTMLElement>("#session-time")!;
const historyList = document.querySelector<HTMLDivElement>("#history")!;

const RecognitionApi = window.SpeechRecognition ?? window.webkitSpeechRecognition;
const recognition = RecognitionApi ? new RecognitionApi() : null;
const CONVERSATION_TIMEOUT_MS = 20_000;

let conversationId = localStorage.getItem("cypher_conversation_id_v2");
let wakeEnabled = true;
let listening = false;
let processing = false;
let awaitingCommand = false;
let selectedVoice: SpeechSynthesisVoice | null = null;
let conversationActiveUntil = 0;
let lastHardwareState = "";
let hardwareOverride: string | null = null;
let recognitionRetryDelayMs = 250;
let recognitionNetworkErrors = 0;
const recentTurns: Array<{ role: "YOU" | "CYPHER"; text: string }> = [];

async function pollNotifications() {
  if (processing) return;
  try {
    const response = await fetch("http://127.0.0.1:8000/notifications");
    if (!response.ok) return;
    const payload = await response.json() as { notifications?: Array<{ text: string }> };
    const notification = payload.notifications?.[0];
    if (!notification?.text) return;
    processing = true;
    activateConversation();
    reply.textContent = notification.text;
    addHistory("CYPHER", notification.text);
    status.textContent = "PROACTIVE GREETING";
    speakText(notification.text, () => {
      processing = false;
      setCoreState(wakeEnabled ? "listening" : "ready");
      startRecognitionSoon();
    });
  } catch {
    // The backend may be restarting; the next poll will retry.
  }
}

function setCoreState(state: "ready" | "listening" | "thinking" | "speaking" | "error") {
  core.dataset.state = state;
  const transientState = {
    ready: "IDLE",
    listening: "PRESENCE",
    thinking: "THINKING",
    speaking: "SUCCESS",
    error: "ALERT",
  }[state];
  const hardwareState = (state === "ready" || state === "listening") && hardwareOverride
    ? hardwareOverride
    : transientState;
  if (hardwareState === lastHardwareState) return;
  lastHardwareState = hardwareState;
  void fetch("http://127.0.0.1:8000/action/status", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: hardwareState }),
  }).catch(() => {
    lastHardwareState = "";
  });
}

function addHistory(role: "YOU" | "CYPHER", text: string) {
  recentTurns.push({ role, text });
  while (recentTurns.length > 8) recentTurns.shift();
  historyList.replaceChildren(
    ...recentTurns.map((turn) => {
      const line = document.createElement("p");
      line.className = "history-line";
      const label = document.createElement("strong");
      label.textContent = turn.role;
      line.append(label, document.createTextNode(turn.text));
      return line;
    }),
  );
  historyList.scrollTop = historyList.scrollHeight;
}

function conversationIsActive() {
  return Date.now() < conversationActiveUntil;
}

function activateConversation() {
  conversationActiveUntil = Date.now() + CONVERSATION_TIMEOUT_MS;
}

function selectVoice() {
  const voices = window.speechSynthesis?.getVoices() ?? [];
  const preferredPatterns = [
    /ryan.*en[-_]?gb/i,
    /george.*en[-_]?gb/i,
    /arthur.*en[-_]?gb/i,
    /daniel.*en[-_]?gb/i,
    /male.*en[-_]?gb/i,
    /en[-_]?gb.*male/i,
    /ryan/i,
    /george/i,
    /arthur/i,
    /daniel/i,
  ];
  selectedVoice = null;
  for (const pattern of preferredPatterns) {
    selectedVoice = voices.find((voice) => pattern.test(`${voice.name} ${voice.lang}`)) ?? null;
    if (selectedVoice) break;
  }
  selectedVoice ??= voices.find((voice) => /^en[-_]?gb$/i.test(voice.lang)) ?? null;
  selectedVoice ??= voices.find((voice) => /^en[-_]/i.test(voice.lang)) ?? null;
  voiceName.textContent = selectedVoice?.name.toUpperCase() ?? "SYSTEM DEFAULT";
}

selectVoice();
if ("speechSynthesis" in window) {
  window.speechSynthesis.addEventListener("voiceschanged", selectVoice);
}

window.setInterval(() => void pollNotifications(), 2_000);

function startRecognitionSoon() {
  if (!recognition || !wakeEnabled || processing || listening) return;
  window.setTimeout(() => {
    if (!wakeEnabled || processing || listening) return;
    try {
      recognition.start();
    } catch {
      status.textContent = "WAKE LISTENER RETRYING";
    }
  }, recognitionRetryDelayMs);
}

function speakText(text: string, after?: () => void) {
  if (!speak.checked || !("speechSynthesis" in window)) {
    after?.();
    return;
  }
  window.speechSynthesis.cancel();
  setCoreState("speaking");
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.voice = selectedVoice;
  utterance.rate = 1.5;
  utterance.pitch = 0.92;
  utterance.onend = () => after?.();
  utterance.onerror = () => after?.();
  window.speechSynthesis.speak(utterance);
}

async function sendMessage(text: string) {
  const cleanText = text.trim();
  if (!cleanText) return;

  processing = true;
  activateConversation();
  setCoreState("thinking");
  if (listening) recognition?.stop();
  transcript.textContent = cleanText;
  addHistory("YOU", cleanText);
  status.textContent = "THINKING";
  listenButton.disabled = true;

  try {
    const response = await fetch("http://127.0.0.1:8000/agent/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: cleanText,
        conversation_id: conversationId,
      }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail ?? `Request failed (${response.status})`);
    }

    const result = (await response.json()) as AgentResponse;
    let afterSpeechAction: (() => void) | null = null;
    if (result.tool?.name === "set_cypher_status" && result.tool.result?.status) {
      hardwareOverride = result.tool.result.status;
    }
    if (result.tool?.name === "play_music") {
      afterSpeechAction = () => window.parent.postMessage({
          type: "CYPHER_PLAY_MUSIC",
          videoId: result.tool?.result?.video_id,
          title: result.tool?.result?.title,
          watchUrl: result.tool?.result?.watch_url,
        }, window.location.origin);
    }
    if (result.tool?.name === "stop_music") {
      afterSpeechAction = () => window.parent.postMessage(
        { type: "CYPHER_STOP_MUSIC" },
        window.location.origin,
      );
    }
    conversationId = result.conversation_id;
    localStorage.setItem("cypher_conversation_id_v2", conversationId);
    reply.textContent = result.reply;
    addHistory("CYPHER", result.reply);
    status.textContent = result.tool
      ? `TOOL // ${result.tool.name.toUpperCase()}`
      : "RESPONSE READY";

    speakText(result.reply, () => {
      afterSpeechAction?.();
      activateConversation();
      processing = false;
      setCoreState(wakeEnabled ? "listening" : "ready");
      listenButton.disabled = false;
      startRecognitionSoon();
    });
  } catch (error) {
    status.textContent = "ERROR";
    setCoreState("error");
    reply.textContent = error instanceof Error ? error.message : "Request failed";
    processing = false;
    listenButton.disabled = false;
    startRecognitionSoon();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = input.value;
  input.value = "";
  void sendMessage(text);
});

if (!recognition) {
  listenButton.disabled = true;
  listenButton.textContent = "VOICE UNAVAILABLE";
  status.textContent = "USE TEXT INPUT";
} else {
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-GB";

  recognition.onstart = () => {
    listening = true;
    recognitionRetryDelayMs = 250;
    setCoreState("listening");
    status.textContent = (awaitingCommand || conversationIsActive())
      ? "CONVERSATION ACTIVE // 20S"
      : "WAKE WORD ARMED";
    listenButton.textContent = "DISABLE WAKE WORD";
    listenButton.classList.add("active");
  };

  recognition.onend = () => {
    listening = false;
    if (!wakeEnabled) {
      listenButton.textContent = "ENABLE WAKE WORD";
      listenButton.classList.remove("active");
      status.textContent = "READY";
      setCoreState("ready");
    } else {
      startRecognitionSoon();
    }
  };

  recognition.onerror = (event) => {
    listening = false;
    if (!wakeEnabled || event.error === "aborted" || event.error === "no-speech") {
      if (!wakeEnabled) {
        status.textContent = "READY";
        setCoreState("ready");
      }
      return;
    }
    if (event.error === "not-allowed" || event.error === "service-not-allowed") {
      wakeEnabled = false;
      status.textContent = "MICROPHONE PERMISSION REQUIRED";
      setCoreState("error");
      listenButton.textContent = "ENABLE WAKE WORD";
      listenButton.classList.remove("active");
      return;
    }
    if (event.error === "network") {
      recognitionNetworkErrors += 1;
      if (recognitionNetworkErrors >= 3) {
        wakeEnabled = false;
        status.textContent = "VOICE SERVICE UNAVAILABLE // OPEN IN EDGE OR CHROME";
        setCoreState("error");
        listenButton.textContent = "ENABLE WAKE WORD";
        listenButton.classList.remove("active");
        return;
      }
      recognitionRetryDelayMs = 2_000;
      status.textContent = "VOICE SERVICE RETRYING";
      setCoreState("error");
      return;
    }
    status.textContent = `VOICE ERROR // ${event.error.toUpperCase()}`;
    setCoreState("error");
  };

  recognition.onresult = (event) => {
    recognitionNetworkErrors = 0;
    const heard = event.results[0]?.[0]?.transcript?.trim() ?? "";
    if (!heard) return;
    transcript.textContent = heard;

    if (awaitingCommand) {
      awaitingCommand = false;
      activateConversation();
      void sendMessage(heard);
      return;
    }

    if (conversationIsActive()) {
      activateConversation();
      void sendMessage(heard);
      return;
    }

    const wakeMatch = /\bcypher\b/i.exec(heard);
    if (!wakeMatch) {
      status.textContent = "WAKE WORD ARMED";
      return;
    }

    const command = heard.slice(wakeMatch.index + wakeMatch[0].length).replace(/^[,\s]+/, "");
    if (command) {
      activateConversation();
      void sendMessage(command);
      return;
    }

    processing = true;
    awaitingCommand = true;
    activateConversation();
    if (listening) recognition.stop();
    reply.textContent = "Hello Ankit. How can I help?";
    addHistory("CYPHER", "Hello Ankit. How can I help?");
    status.textContent = "WAKE WORD DETECTED";
    speakText("Hello Ankit. How can I help?", () => {
      activateConversation();
      processing = false;
      startRecognitionSoon();
    });
  };

  listenButton.textContent = "DISABLE WAKE WORD";
  listenButton.classList.add("active");
  startRecognitionSoon();
  listenButton.addEventListener("click", () => {
    wakeEnabled = !wakeEnabled;
    awaitingCommand = false;
    recognitionRetryDelayMs = 250;
    recognitionNetworkErrors = 0;
    if (wakeEnabled) {
      startRecognitionSoon();
    } else {
      conversationActiveUntil = 0;
      status.textContent = "READY";
      setCoreState("ready");
      listenButton.textContent = "ENABLE WAKE WORD";
      listenButton.classList.remove("active");
      if (listening) recognition.stop();
    }
  });

  window.setInterval(() => {
    const remaining = Math.max(
      0,
      Math.ceil((conversationActiveUntil - Date.now()) / 1000),
    );
    sessionTime.textContent = remaining > 0 ? `${remaining} SEC` : "WAKE WORD";

    if (
      wakeEnabled
      && !processing
      && !awaitingCommand
      && !conversationIsActive()
      && status.textContent?.startsWith("CONVERSATION ACTIVE")
    ) {
      status.textContent = "WAKE WORD ARMED";
    }
  }, 500);
}
