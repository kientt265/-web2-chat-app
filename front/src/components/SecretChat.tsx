import  { useEffect, useState } from "react";
import { ec } from "elliptic";

const ecdh = new ec("curve25519");

export default function App() {
  const [privateKey, setPrivateKey] = useState<string | null>(null);
  const [publicKey, setPublicKey] = useState<string | null>(null);

  // Tạo key pair hoặc load từ localStorage
  useEffect(() => {
    const storedPriv = localStorage.getItem("privateKey");
    const storedPub = localStorage.getItem("publicKey");

    if (storedPriv && storedPub) {
      setPrivateKey(storedPriv);
      setPublicKey(storedPub);
    } else {
      const key = ecdh.genKeyPair();
      const priv = key.getPrivate("hex");
      const pub = key.getPublic("hex");

      localStorage.setItem("privateKey", priv);
      localStorage.setItem("publicKey", pub);

      setPrivateKey(priv);
      setPublicKey(pub);
    }
  }, []);

  // Ví dụ: derive secret key khi nhận được pubKey của user khác
  const deriveSecret = (otherPubHex: string) => {
    if (!privateKey) return null;
    const myKey = ecdh.keyFromPrivate(privateKey, "hex");
    const otherKey = ecdh.keyFromPublic(otherPubHex, "hex");
    const secret = myKey.derive(otherKey.getPublic()).toString(16);
    return secret;
  };

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold">E2EE Key Demo</h1>
      <p>Private Key: {privateKey}</p>
      <p>Public Key: {publicKey}</p>

      <button
        className="mt-2 px-3 py-1 bg-blue-500 text-white rounded"
        onClick={() => {
          // Giả sử nhận được public key của B
          const otherPub = "abcdef1234567890"; // demo
          const secret = deriveSecret(otherPub);
          alert("Derived secret: " + secret);
        }}
      >
        Derive Secret
      </button>
    </div>
  );
}
