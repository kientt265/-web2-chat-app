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
  return { priv, pub };
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
function hexToUint8Array(hexString: string): Uint8Array {
  if (hexString.length % 2 !== 0) {
    throw new Error("Invalid hex string");
  }
  const array = new Uint8Array(hexString.length / 2);
  for (let i = 0; i < hexString.length; i += 2) {
    array[i / 2] = parseInt(hexString.substr(i, 2), 16);
  }
  return array;
}


export const encryptMessage = async (conversationId: string, otherPubHex: string, message: string) => {
  try {
    const shareKeyString = deriveSecret(conversationId, otherPubHex);
    if (!shareKeyString) {
      console.error('Failed to derive shared key');
      return message;
    }

    const shareKey = hexToUint8Array(shareKeyString);
    // Kiểm tra độ dài của shareKey
    if (shareKey.length !== 32) { // AES-256 yêu cầu khóa 32 bytes
      console.error('Invalid shared key length');
      return message;
    }

    const encoder = new TextEncoder();
    const messageBytes = encoder.encode(message);
    const iv = window.crypto.getRandomValues(new Uint8Array(12));

    try {
      const key = await window.crypto.subtle.importKey(
        'raw',
        shareKey,
        { name: 'AES-GCM' },
        false,
        ['encrypt']
      );

      const encryptedData = await window.crypto.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        key,
        messageBytes
      );

      const encryptedArray = new Uint8Array(iv.length + encryptedData.byteLength);
      encryptedArray.set(iv);
      encryptedArray.set(new Uint8Array(encryptedData), iv.length);

      return btoa(String.fromCharCode(...encryptedArray));
    } catch (cryptoError) {
      console.error('Encryption operation failed:', cryptoError);
      return message;
    }
  } catch (error) {
    console.error('Failed to encrypt message:', error);
    return message;
  }
}

 export const  decryptMessage = async (conversationId: string, otherPubHex: string, encryptedMessage: string) => {
  try {
    if(encryptedMessage.startsWith('http://') || encryptedMessage.startsWith('https://')) return encryptedMessage;
    const shareKeyString = deriveSecret(conversationId, otherPubHex);
    if (shareKeyString) {

      const shareKey = hexToUint8Array(shareKeyString);
      console.log(`Shared Key: ${shareKey}`)
      if (!shareKey) return encryptedMessage;

      // Chuyển đổi từ Base64 về dạng binary
      const encryptedArray = new Uint8Array(
        atob(encryptedMessage).split('').map(char => char.charCodeAt(0))
      );

      // Tách IV và dữ liệu đã mã hóa
      const iv = encryptedArray.slice(0, 12);
      const encryptedData = encryptedArray.slice(12);

      // Import shareKey
      const key = await window.crypto.subtle.importKey(
        'raw',
        shareKey,
        { name: 'AES-GCM' },
        false,
        ['decrypt']
      );

      // Giải mã tin nhắn
      const decryptedData = await window.crypto.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        key,
        encryptedData
      );

      // Chuyển đổi kết quả về dạng text
      const decoder = new TextDecoder();
      return decoder.decode(decryptedData);
    } else {
      return encryptedMessage ?? "";;
    }
  } catch (error) {
    console.error('Failed to decrypt message:', error);
    return encryptedMessage ?? "";
  }
}