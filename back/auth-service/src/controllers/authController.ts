import { Request, Response } from 'express';

import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { sendUserCreatedEvent } from '../kafka/producer';

const prisma = new PrismaClient();
const JWT_SECRET = 'your-secret-key'; 
export const register = async (req: Request, res: Response) => {
  const { username, email, password } = req.body;

  try {
    const password_hash = await bcrypt.hash(password, 10);
    const user = await prisma.users.create({
      data: {
        username,
        email,
        password_hash,
      },
    });
    // Push event to Kafka
    await sendUserCreatedEvent({ user_id: user.user_id, username, email });
    res.status(201).json({ user_id: user.user_id, username, email });
  } catch (error) {
    console.error('Error registering user:', error);
    res.status(500).json({ error: `Failed to register ${error}`});
  }
};

export const login = async (req: Request, res: Response) => {
  const { email, password } = req.body;

  try {
    const user = await prisma.users.findUnique({ where: { email } });
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const isValidPassword = await bcrypt.compare(password, user.password_hash);
    if (!isValidPassword) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = jwt.sign({ user_id: user.user_id }, JWT_SECRET, { expiresIn: '1h' });
    res.status(200).json({ token, user_id: user.user_id, username: user.username });
  } catch (error) {
    console.error('Error logging in:', error);
    res.status(500).json({ error: 'Failed to login' });
  }
};