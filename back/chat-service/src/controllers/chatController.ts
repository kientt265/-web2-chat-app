import { Request, Response } from 'express';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

interface UserMember {
  user_id: string;
  pubkey?: string | null;
}

export const getMessages = async (req: Request, res: Response) => {
  const { conversation_id } = req.params;

  try {
    const messages = await prisma.messages.findMany({
      where: { conversation_id },
      orderBy: { sent_at: 'asc' },
      include: {
        // sender: { select: { user_id: true, username: true } }, // Removed because 'sender' relation does not exist
      },
    });
    res.status(200).json(messages);
  } catch (error) {
    console.error('Error fetching messages:', error);
    res.status(500).json({ error: 'Failed to fetch messages' });
  }
};


export const createConversation = async (req: Request, res: Response) => {
  const { type, name, user_ids, subtype, pubkey } = req.body as {
    type: 'private' | 'group';
    name?: string;
    user_ids: UserMember[];
    subtype?: 'normal' | 'secret';
    pubkey?: string;
  };


  try {

    if (type === 'private' && name) {
      return res.status(400).json({ error: 'Private conversations cannot have a name' });
    }
    if (type === 'group' && !name) {
      return res.status(400).json({ error: 'Group conversations must have a name' });
    }

    if (type === 'private' && !subtype) {
      return res.status(400).json({ error: 'Private conversations must have a subtype (normal or secret)' });
    }
    if (type !== 'private' && subtype) {
      return res.status(400).json({ error: 'Only private conversations can have a subtype' });
    }

    const host_user_id = req.user?.user_id!;

    user_ids.push({ user_id: host_user_id, pubkey });

    const conversation = await prisma.conversations.create({
      data: {
        type,
        name,
        subtype: type === 'private' ? subtype : null,
        members: {
          create: user_ids.map(({ user_id, pubkey }) => ({
            user_id,
            pubkey:
              type === 'private' && subtype === 'secret' && user_id === host_user_id
                ? pubkey
                : null,
            joined_at: new Date(),
          })),
        },
      },
      include: { members: true },
    });

    res.status(201).json(conversation);
  } catch (error) {
    console.error('Error creating conversation:', error);
    res.status(500).json({ error: 'Failed to create conversation' });
  }
};

export const acceptSecretConversation = async (req: Request, res: Response) => {
  const { conversation_id, pubkey } = req.body;

  if (!req.user?.user_id) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  const user_id = req.user.user_id;

  try {
    const conversation = await prisma.conversations.findUnique({
      where: { conversation_id },
    });

    if (!conversation) {
      return res.status(404).json({ error: "Conversation not found" });
    }

    if (conversation.type !== "private" || conversation.subtype !== "secret") {
      return res.status(400).json({ error: "Not a secret private conversation" });
    }

    const member = await prisma.conversation_members.findUnique({
      where: {
        conversation_id_user_id: {
          conversation_id,
          user_id,
        },
      },
    });

    if (!member) {
      return res.status(403).json({ error: "You are not a member of this conversation" });
    }

    if (member.pubkey) {
      return res.status(400).json({ error: "Pubkey already set" });
    }

    const updatedMember = await prisma.conversation_members.update({
      where: {
        conversation_id_user_id: {
          conversation_id,
          user_id,
        },
      },
      data: { pubkey },
    });

    return res.status(200).json({
      message: "Pubkey added successfully",
      member: updatedMember,
    });
  } catch (error) {
    console.error("Error accepting secret conversation:", error);
    return res.status(500).json({ error: "Failed to accept conversation" });
  }
};

export const sendMessage = async (req: Request, res: Response) => {
  const { conversation_id, sender_id, content } = req.body;

  try {
    const member = await prisma.conversation_members.findFirst({
      where: {
        conversation_id,
        user_id: sender_id
      }
    });

    if (!member) {
      return res.status(403).json({ error: 'User is not a member of this conversation' });
    }

    const message = await prisma.messages.create({
      data: {
        conversation_id,
        sender_id,
        content,
        sent_at: new Date(),
      }
    });

    res.status(201).json(message);
  } catch (error) {
    console.error('Error sending message:', error);
    res.status(500).json({ error: 'Failed to send message' });
  }
};

export const getAllConversations = async (req: Request, res: Response) => {
  try {
    const user_id = req.user?.user_id;

    if (!user_id) {
      return res.status(401).json({ error: 'User not authenticated' });
    }

    const conversations = await prisma.conversations.findMany({
      where: {
        members: {
          some: {
            user_id: user_id
          }
        }
      },
      include: {
        members: true,
        messages: {
          orderBy: {
            sent_at: 'desc'
          },
          take: 1,
        }
      },
      orderBy: {
        created_at: 'desc'
      }
    });

    const formattedConversations = conversations.map(conv => ({
      conversation_id: conv.conversation_id,
      type: conv.type,
      name: conv.name,
      created_at: conv.created_at,
      member_count: conv.members.length,
      members: conv.members,
      last_message: conv.messages[0] || null
    }));

    res.status(200).json(formattedConversations);
  } catch (error) {
    console.error('Error fetching conversations:', error);
    res.status(500).json({ error: 'Failed to fetch conversations' });
  }
};