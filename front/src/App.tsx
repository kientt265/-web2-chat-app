
import { Routes, Route } from 'react-router-dom';
import Login from './pages/public/Login.tsx';
import Signup from './pages/public/SignUp.tsx';
import Chat from './pages/public/ChatPage.tsx';
import Test from './pages/public/Test.tsx';
function App() {

  return (
    <Routes>
        <Route path="/" element={<Login/>} />
        <Route path="/Signup" element={<Signup/>} />
        <Route path="/Chat" element={<Chat/>} />
        <Route path="/Test" element={<Test/>} />
    </Routes>
  )
}

export default App
