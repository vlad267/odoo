from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

# Приклад базової моделі
class PracticeTask(models.Model):
    _name = 'practice.task'
    _description = 'Завдання для практики'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    # Базові поля
    name = fields.Char('Назва', required=True, tracking=True)
    description = fields.Text('Опис')
    sequence = fields.Integer('Послідовність', default=10)
    state = fields.Selection([
        ('draft', 'Чернетка'),
        ('progress', 'У процесі'),
        ('done', 'Виконано'),
        ('cancel', 'Скасовано')
    ], string='Стан', default='draft', tracking=True)
    
    # Поля з відносинами
    user_id = fields.Many2one('res.users', string='Відповідальний', default=lambda self: self.env.user)
    tag_ids = fields.Many2many('practice.tag', string='Теги')
    task_line_ids = fields.One2many('practice.task.line', 'task_id', string='Рядки завдань')
    
    # Обчислювані поля
    task_count = fields.Integer(compute='_compute_task_count', string='Кількість підзавдань')
    is_late = fields.Boolean(compute='_compute_is_late', string='Запізнено')
    
    # Спеціальні поля
    start_date = fields.Date('Дата початку')
    end_date = fields.Date('Дата завершення')
    duration = fields.Float('Тривалість (години)')
    color = fields.Integer('Колір')
    priority = fields.Selection([
        ('0', 'Низька'),
        ('1', 'Нормальна'),
        ('2', 'Висока'),
        ('3', 'Дуже висока')
    ], string='Пріоритет', default='1')
    attachment_ids = fields.Many2many('ir.attachment', string='Вкладення')
    
    # SQL constraints
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Назва завдання повинна бути унікальною!'),
        ('check_dates', 'CHECK(end_date >= start_date)', 'Дата завершення повинна бути після дати початку!')
    ]
    
    # Обчислення полів
    @api.depends('task_line_ids')
    def _compute_task_count(self):
        for task in self:
            if task.task_line_ids:
                task.task_count = len(task.task_line_ids)  # type: ignore
            else:
                task.task_count = 0
    
    @api.depends('end_date')
    def _compute_is_late(self):
        today = fields.Date.today()
        for task in self:
            if task.end_date and task.state != 'done':
                task.is_late = task.end_date < today  # type: ignore
            else:
                task.is_late = False
    
    # Onchange методи
    @api.onchange('start_date', 'end_date')
    def _onchange_dates(self):
        if self.start_date and self.end_date:
            # Конвертуємо дати у datetime.date для обчислення різниці
            start_date = self.start_date
            end_date = self.end_date
            if isinstance(start_date, fields.Date):
                start_date = fields.Date.from_string(start_date)
            if isinstance(end_date, fields.Date):
                end_date = fields.Date.from_string(end_date)
            
            delta_days = (end_date - start_date).days
            self.duration = delta_days * 8  # 8 годин на день
    
    # CRUD методи (перевизначення)
    @api.model
    def create(self, vals):
        # Додаємо префікс до назви
        if vals.get('name'):
            vals['name'] = f"TASK-{vals['name']}"
        return super(PracticeTask, self).create(vals)
    
    def write(self, vals):
        # Логіка при оновленні записів
        return super(PracticeTask, self).write(vals)
    
    def unlink(self):
        # Перевірка перед видаленням
        for task in self:
            if task.state != 'draft':
                raise UserError(_('Не можна видалити завдання, яке не у стані чернетки!'))
        return super(PracticeTask, self).unlink()
    
    # Методи дій (buttons)
    def action_progress(self):
        for task in self:
            task.state = 'progress'
    
    def action_done(self):
        for task in self:
            if not task.task_line_ids:
                raise ValidationError(_('Не можна завершити завдання без підзавдань!'))
            task.state = 'done'
    
    def action_cancel(self):
        for task in self:
            task.state = 'cancel'
    
    def action_draft(self):
        for task in self:
            task.state = 'draft'
    
    # Планувальники (cron)
    @api.model
    def _cron_check_late_tasks(self):
        # Метод, який можна запускати в планувальнику
        late_tasks = self.search([
            ('end_date', '<', fields.Date.today()),
            ('state', 'in', ['draft', 'progress'])
        ])
        for task in late_tasks:
            task.message_post(body=_('Завдання прострочено!'))
    
    # Обчисленя default
    @api.model
    def _default_stage_id(self):
        # Метод для обчислення значення за замовчуванням
        return self.env['practice.stage'].search([], limit=1)

    # Додатковий метод для кнопки відображення підзавдань
    def action_view_task_lines(self):
        self.ensure_one()
        return {
            'name': _('Підзавдання'),
            'type': 'ir.actions.act_window',
            'res_model': 'practice.task.line',
            'view_mode': 'tree,form',
            'domain': [('task_id', '=', self.id)],
            'context': {'default_task_id': self.id},
        }


# Модель для підзавдань
class PracticeTaskLine(models.Model):
    _name = 'practice.task.line'
    _description = 'Підзавдання'
    
    name = fields.Char('Назва', required=True)
    task_id = fields.Many2one('practice.task', string='Завдання', required=True)
    is_done = fields.Boolean('Виконано', default=False)
    user_id = fields.Many2one('res.users', string='Виконавець')
    deadline = fields.Date('Кінцевий термін')
    notes = fields.Text('Примітки')
    
    @api.onchange('is_done')
    def _onchange_is_done(self):
        if self.is_done:
            self.notes = f"{self.notes or ''}\nВиконано: {fields.Datetime.now()}"


# Модель для тегів
class PracticeTag(models.Model):
    _name = 'practice.tag'
    _description = 'Теги для завдань'
    
    name = fields.Char('Назва', required=True)
    color = fields.Integer('Колір')
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Назва тегу має бути унікальною!')
    ]


# Модель для етапів
class PracticeStage(models.Model):
    _name = 'practice.stage'
    _description = 'Етапи завдань'
    _order = 'sequence'
    
    name = fields.Char('Назва', required=True)
    sequence = fields.Integer('Послідовність', default=10)
    fold = fields.Boolean('Згорнуто на kanban')
    description = fields.Text('Опис')