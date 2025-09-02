import { Router } from 'express';
import { getMessages, sendImage, updateLastSeenMsg, createConversation, sendMessage, leavingConversations, getAllConversations, acceptSecretConversation } from '../controllers/chatController';
import { authMiddleware } from '../middleware/auth';
import upload from '../config/customMulter';

const router = Router();

router.use(authMiddleware); 

router.get('/messages/:conversation_id', getMessages);
router.post('/conversation', createConversation);
router.post('/messages', sendMessage);
router.get('/conversations', getAllConversations);
router.patch('/conversations/:conversation_id/accept', acceptSecretConversation);
router.delete('/conversations/:conversation_id', leavingConversations);
router.post('/conversations/:conversation_id/upload', upload.single("file"), sendImage);
router.post('/conversations/update_last_read_msg', updateLastSeenMsg);

export default router;