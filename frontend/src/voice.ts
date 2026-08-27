import "./voice.css";

type AgentResponse = {
  conversation_id: string;
  reply: string;
  tool: { name: string } | null;
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

const RecognitionApi = window.SpeechRecognition ?? window.webkitSpeechRecognition;
const recognition = RecognitionApi ? new RecognitionApi() : null;
const CONVERSATION_TIMEOUT_MS = 20_000;

let conversationId = localStorage.getItem("cypher_conversation_id_v2");
let wakeEnabled = false;
let listening = false;
let processing = false;
let awaitingCommand = false;
let selectedVoice: SpeechSynthesisVoice | null = null;
let conversationActiveUntil = 0;

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
}

selectVoice();
if ("speechSynthesis" in window) {
  window.speechSynthesis.addEventListener("voiceschanged", selectVoice);
}

function startRecognitionSoon() {
  if (!recognition || !wakeEnabled || processing || listening) return;
  window.setTimeout(() => {
    if (!wakeEnabled || processing || listening) return;
    try {
      recognition.start();
    } catch {
      status.textContent = "WAKE LISTENER RETRYING";
    }
  }, 250);
}

function speakText(text: string, after?: () => void) {
  if (!speak.checked || !("speechSynthesis" in window)) {
    after?.();
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.voice = selectedVoice;
  utterance.rate = 1;
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
  if (listening) recognition?.stop();
  transcript.textContent = cleanText;
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
    conversationId = result.conversation_id;
    localStorage.setItem("cypher_conversation_id_v2", conversationId);
    reply.textContent = result.reply;
    status.textContent = result.tool
      ? `TOOL // ${result.tool.name.toUpperCase()}`
      : "RESPONSE READY";

    speakText(result.reply, () => {
      activateConversation();
      processing = false;
      listenButton.disabled = false;
      startRecognitionSoon();
    });
  } catch (error) {
    status.textContent = "ERROR";
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
    } else {
      startRecognitionSoon();
    }
  };

  recognition.onerror = (event) => {
    if (event.error === "not-allowed" || event.error === "service-not-allowed") {
      wakeEnabled = false;
      status.textContent = "MICROPHONE PERMISSION REQUIRED";
      listenButton.textContent = "ENABLE WAKE WORD";
      listenButton.classList.remove("active");
      return;
    }
    if (event.error !== "no-speech") {
      status.textContent = `VOICE ERROR // ${event.error.toUpperCase()}`;
    }
  };

  recognition.onresult = (event) => {
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
    status.textContent = "WAKE WORD DETECTED";
    speakText("Hello Ankit. How can I help?", () => {
      activateConversation();
      processing = false;
      startRecognitionSoon();
    });
  };

  listenButton.textContent = "ENABLE WAKE WORD";
  listenButton.addEventListener("click", () => {
    wakeEnabled = !wakeEnabled;
    awaitingCommand = false;
    if (!wakeEnabled) conversationActiveUntil = 0;
    if (wakeEnabled) startRecognitionSoon();
    else if (listening) recognition.stop();
  });

  window.setInterval(() => {
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
