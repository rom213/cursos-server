require('dotenv').config();
const express = require('express');
const cron = require('node-cron');
const { google } = require('googleapis');

const app = express();
app.use(express.json());


let tareasPendientes = [];

const auth = new google.auth.GoogleAuth({
  keyFile: 'credentials.json',
  scopes: ['https://www.googleapis.com/auth/admin.directory.group']
});

const service = google.admin({ version: 'directory_v1', auth });

/**
 * Endpoint para recibir la data del usuario a eliminar.
 * Se espera recibir un JSON con:
 * {
 *    "group_email": "grupo@dominio.com",
 *    "member_email": "usuario@dominio.com"
 * }
 */
app.post('/schedule', (req, res) => {
  const { group_email, member_email } = req.body;

  if (!group_email || !member_email) {
    return res.status(400).json({
      error: 'Se requieren los campos group_email y member_email'
    });
  }

  // Programar la eliminación en 10 minutos
  const scheduledTime = new Date(Date.now() + 1 * 60 * 1000);

  tareasPendientes.push({ group_email, member_email, scheduledTime });
  console.log(
    `Programado: Eliminar al miembro ${member_email} del grupo ${group_email} a las ${scheduledTime}`
  );

  return res.json({
    message: 'Tarea programada para eliminar al miembro en 3 minutos'
  });
});

/**
 * Cron job que se ejecuta cada minuto para revisar las tareas pendientes.
 */
cron.schedule('* * * * *', async () => {
  console.log('Ejecutando cron para revisar tareas pendientes...');
  const now = new Date();

  // Extraer las tareas que ya están vencidas (scheduledTime <= ahora)
  const tareasAVerificar = tareasPendientes.filter(tarea => now >= tarea.scheduledTime);

  // Para cada tarea vencida, llamar a la API para eliminar al miembro del grupo
  for (const tarea of tareasAVerificar) {
    try {
      await service.members.delete({
        groupKey: tarea.group_email,
        memberKey: tarea.member_email
      });
      console.log(
        `Eliminado: Miembro ${tarea.member_email} eliminado del grupo ${tarea.group_email}`
      );
    } catch (error) {
      console.error(
        `Error al eliminar al miembro ${tarea.member_email} del grupo ${tarea.group_email}:`,
        error.response ? error.response.data : error.message
      );
    }
  }

  // Remover las tareas que ya se procesaron
  tareasPendientes = tareasPendientes.filter(tarea => now < tarea.scheduledTime);
});

// Iniciar el servidor
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Servidor de eliminación corriendo en http://localhost:${PORT}`);
});
