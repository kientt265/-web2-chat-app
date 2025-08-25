import { Router } from 'express';
import { getMessages, createConversation, sendMessage, getAllConversations, acceptSecretConversation } from '../controllers/chatController';
import { authMiddleware } from '../middleware/auth';

const router = Router();

router.use(authMiddleware); 

router.get('/messages/:conversation_id', getMessages);
router.post('/conversation', createConversation);
router.post('/messages', sendMessage);
router.get('/conversations', getAllConversations);
router.patch('/conversations/:conversation_id/accept', acceptSecretConversation);

export default router;