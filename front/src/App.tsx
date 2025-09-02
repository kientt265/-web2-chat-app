
import { Routes, Route } from 'react-router-dom';
import Login from './pages/public/Login.tsx';
import Signup from './pages/public/SignUp.tsx';
import Chat from './pages/public/ChatPage.tsx';
function App() {

  return (
    <Routes>
        <Route path="/" element={<Login/>} />
        <Route path="/Signup" element={<Signup/>} />
        <Route path="/Chat" element={<Chat/>} />
    </Routes>
  )
}

export default App
