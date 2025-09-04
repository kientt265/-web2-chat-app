import { Routes, Route } from 'react-router-dom';
import Login from '../pages/public/Login.tsx';
import Signup from '../pages/public/SignUp.tsx';
import Chat from '../pages/public/ChatPage.tsx';

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/chat" element={<Chat />} />
    </Routes>
  );
};

export default AppRoutes;
