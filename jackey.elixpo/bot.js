import { Client, PermissionsBitField } from 'discord.js';
import dotenv from 'dotenv';

dotenv.config();

const PERMISSIONS = PermissionsBitField.Flags;
const getPermissionName = (flagValue) => {
    const name = Object.keys(PERMISSIONS).find(key => PERMISSIONS[key] === flagValue);
    return name || 'Unknown Permission';
};

const client = new Client({
    intents: ['Guilds', 'GuildMessages', 'MessageContent'],
});


// Handle both ready and clientReady events for compatibility
const readyHandler = async () => {
    console.log(`${client.user.tag} is online and ready!`);
    client.user.setActivity("Pixels in the sky!", { type: 4 }); 

    const activityInterval = setInterval(() => {
        const activities = [
            { name: "Pixels in the sky!", type: 4 }, 
            { name: "The Palette and Canvas", type: 0 }, 
            { name: "Synthwave of Pixels!", type: 3 }, 
        ];
        const randomActivity = activities[Math.floor(Math.random() * activities.length)];
        client.user.setActivity(randomActivity.name, { type: randomActivity.type });
    }, 10 * 60 * 1000);
};

// Register event handlers for both current and future discord.js versions
client.on('ready', readyHandler);
client.on('clientReady', readyHandler);

export { client, PERMISSIONS, getPermissionName };