import { ec } from "elliptic";
const ecdh = new ec("curve25519");

const LOCAL_KEY = "conversationKeys";


function loadKeys() {
  const data = localStorage.getItem(LOCAL_KEY);
  return data ? JSON.parse(data) : {};
}


function saveKeys(keys: any) {
  localStorage.setItem(LOCAL_KEY, JSON.stringify(keys));
}


export function generateConversationKey() {
  const keyPair = ecdh.genKeyPair();
  const priv = keyPair.getPrivate("hex");
  const pub = keyPair.getPublic("hex");
  return {priv, pub};
}

export function saveKeyLocalStorage(convId: string, priv: string, pub: string) {
  const keys = loadKeys();
  if (keys[convId]) {
    return keys[convId];
  }
  keys[convId] = { privateKey: priv, publicKey: pub };
  saveKeys(keys);

  return true;
}


export function getConversationKey(convId: string) {
  const keys = loadKeys();
  return keys[convId] || null;
}


export function deriveSecret(convId: string, otherPubHex: string) {
  const myKeys = getConversationKey(convId);
  if (!myKeys) return null;

  const myKey = ecdh.keyFromPrivate(myKeys.privateKey, "hex");
  const otherKey = ecdh.keyFromPublic(otherPubHex, "hex");

  const secret = myKey.derive(otherKey.getPublic()).toString(16);
  return secret;
}
