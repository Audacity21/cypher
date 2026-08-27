import "./voice.css";

type AgentResponse = {
  conversation_id: string;
  reply: string;
  tool: { name: string } | null;
};

type SpeechRecognitionEventLike = Event & {
  results: ArrayLike<{
    0: { transcript: string };
  }>;
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

let conversationId = localStorage.getItem("cypher_conversation_id");
let listening = false;

async function sendMessage(text: string) {
  const cleanText = text.trim();
  if (!cleanText) return;

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
    localStorage.setItem("cypher_conversation_id", conversationId);
    reply.textContent = result.reply;
    status.textContent = result.tool
      ? `TOOL // ${result.tool.name.toUpperCase()}`
      : "RESPONSE READY";

    if (speak.checked && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(result.reply);
      utterance.rate = 1;
      utterance.pitch = 0.9;
      window.speechSynthesis.speak(utterance);
    }
  } catch (error) {
    status.textContent = "ERROR";
    reply.textContent = error instanceof Error ? error.message : "Request failed";
  } finally {
    listenButton.disabled = false;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = input.value;
  input.value = "";
  void sendMessage(text);
});

const RecognitionApi =
  window.SpeechRecognition ?? window.webkitSpeechRecognition;

if (!RecognitionApi) {
  listenButton.disabled = true;
  listenButton.textContent = "VOICE UNAVAILABLE";
  status.textContent = "USE TEXT INPUT";
} else {
  const recognition = new RecognitionApi();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-IN";

  recognition.onstart = () => {
    listening = true;
    status.textContent = "LISTENING";
    listenButton.textContent = "STOP LISTENING";
    listenButton.classList.add("active");
  };

  recognition.onend = () => {
    listening = false;
    listenButton.textContent = "START LISTENING";
    listenButton.classList.remove("active");
    if (status.textContent === "LISTENING") status.textContent = "READY";
  };

  recognition.onerror = (event) => {
    status.textContent = `VOICE ERROR // ${event.error.toUpperCase()}`;
  };

  recognition.onresult = (event) => {
    const text = event.results[0]?.[0]?.transcript ?? "";
    void sendMessage(text);
  };

  listenButton.addEventListener("click", () => {
    if (listening) recognition.stop();
    else recognition.start();
  });
}
