"""
节点图形组件
用于在画板上显示和交互的节点
"""
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsTextItem, 
                               QGraphicsRectItem, QGraphicsEllipseItem,
                               QMenu, QGraphicsSceneMouseEvent)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QFont, QPainter

from src.core.node_base import NodeType


class NodeGraphicsItem(QGraphicsItem):
    """节点图形项"""
    
    # 节点类型对应的颜色
    NODE_COLORS = {
        NodeType.VARIABLE_ASSIGN: "#4CAF50",    # 绿色
        NodeType.VARIABLE_CALC: "#2196F3",      # 蓝色
        NodeType.SQLITE_CONNECT: "#FF9800",     # 橙色
        NodeType.SQLITE_EXECUTE: "#9C27B0",     # 紫色
        NodeType.SQL_STATEMENT: "#00BCD4",      # 青色
    }
    
    def __init__(self, node_id: str, node_type: NodeType, title: str = None, parent=None):
        """
        初始化节点图形项
        
        Args:
            node_id: 节点ID
            node_type: 节点类型
            title: 节点标题
            parent: 父项
        """
        super().__init__(parent)
        
        self.node_id = node_id
        self.node_type = node_type
        self.title = title or node_type.value
        self.config = {}  # 节点配置
        
        # 尺寸
        self.width = 180
        self.height = 80
        self.header_height = 30
        self.corner_radius = 8
        
        # 颜色
        self.color = QColor(self.NODE_COLORS.get(node_type, "#607D8B"))
        self.header_color = self.color.darker(110)
        self.body_color = QColor("#2d2d2d")
        self.border_color = QColor("#3f3f3f")
        self.selected_color = QColor("#0e639c")
        
        # 状态
        self.is_selected = False
        self.is_executing = False
        self.is_error = False
        
        # 选中的画笔
        self.selected_pen = QPen(self.selected_color, 3)
        
        # 设置标志
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        
        # 创建文本项
        self._create_text_items()
        
        # 输入输出端口
        self.input_ports = []
        self.output_ports = []
        self._create_ports()
    
    def _create_text_items(self):
        """创建文本项"""
        # 标题文本
        self.title_item = QGraphicsTextItem(self.title, self)
        self.title_item.setDefaultTextColor(QColor("#ffffff"))
        font = QFont("Arial", 10, QFont.Bold)
        self.title_item.setFont(font)
        
        # 居中标题
        title_width = self.title_item.boundingRect().width()
        self.title_item.setPos(
            (self.width - title_width) / 2,
            (self.header_height - self.title_item.boundingRect().height()) / 2
        )
        
        # 节点类型文本
        self.type_item = QGraphicsTextItem(self.node_type.value, self)
        self.type_item.setDefaultTextColor(QColor("#a0a0a0"))
        font = QFont("Arial", 8)
        self.type_item.setFont(font)
        
        # 居中类型
        type_width = self.type_item.boundingRect().width()
        self.type_item.setPos(
            (self.width - type_width) / 2,
            self.header_height + 10
        )
    
    def _create_ports(self):
        """创建输入输出端口"""
        port_radius = 6
        
        # 输入端口（左侧）
        input_port = PortGraphicsItem(
            self, 
            PortType.INPUT, 
            QPointF(0, self.height / 2),
            port_radius
        )
        self.input_ports.append(input_port)
        
        # 输出端口（右侧）
        output_port = PortGraphicsItem(
            self,
            PortType.OUTPUT,
            QPointF(self.width, self.height / 2),
            port_radius
        )
        self.output_ports.append(output_port)
    
    def boundingRect(self) -> QRectF:
        """返回边界矩形"""
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter: QPainter, option, widget=None):
        """绘制节点"""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 选中状态边框（使用Qt的选中状态）
        if self.isSelected():
            painter.setPen(self.selected_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                -2, -2, 
                self.width + 4, self.height + 4,
                self.corner_radius, self.corner_radius
            )
        
        # 绘制主体
        painter.setPen(QPen(self.border_color, 1))
        painter.setBrush(QBrush(self.body_color))
        painter.drawRoundedRect(
            0, 0, self.width, self.height,
            self.corner_radius, self.corner_radius
        )
        
        # 绘制头部
        painter.setBrush(QBrush(self.header_color))
        painter.drawRoundedRect(
            0, 0, self.width, self.header_height,
            self.corner_radius, self.corner_radius
        )
        
        # 绘制头部底部的矩形（覆盖圆角）
        painter.setPen(Qt.NoPen)
        painter.drawRect(
            0, self.header_height - self.corner_radius,
            self.width, self.corner_radius
        )
        
        # 执行状态指示
        if self.is_executing:
            painter.setPen(QPen(QColor("#4CAF50"), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                0, 0, self.width, self.height,
                self.corner_radius, self.corner_radius
            )
        
        # 错误状态指示
        if self.is_error:
            painter.setPen(QPen(QColor("#f44336"), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                0, 0, self.width, self.height,
                self.corner_radius, self.corner_radius
            )
    
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        """鼠标按下事件"""
        # 让Qt处理选中状态
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """鼠标释放事件"""
        super().mouseReleaseEvent(event)
    
    def itemChange(self, change, value):
        """处理项目变化"""
        if change == QGraphicsItem.ItemSelectedHasChanged:
            # 选中状态改变时更新显示
            self.update()
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        """右键菜单事件"""
        menu = QMenu()
        
        execute_action = menu.addAction("执行节点")
        config_action = menu.addAction("配置节点")
        menu.addSeparator()
        delete_action = menu.addAction("删除节点")
        
        action = menu.exec_(event.screenPos())
        
        if action == execute_action:
            self.execute_node()
        elif action == config_action:
            self.configure_node()
        elif action == delete_action:
            self.delete_node()
    
    def execute_node(self):
        """执行节点"""
        print(f"执行节点: {self.node_id}")
        self.is_executing = True
        self.update()
        # TODO: 实际执行逻辑
    
    def configure_node(self):
        """配置节点"""
        print(f"配置节点: {self.node_id}")
        # TODO: 打开配置对话框
    
    def delete_node(self):
        """删除节点"""
        print(f"删除节点: {self.node_id}")
        
        # 删除所有相关连接
        for port in self.input_ports + self.output_ports:
            for connection in port.connections[:]:  # 复制列表以避免迭代时修改
                scene = connection.scene()
                if scene:
                    scene.removeItem(connection)
        
        # 从场景中移除节点
        scene = self.scene()
        if scene:
            # 通知Canvas节点被删除（让WorkflowTabWidget清理数据）
            # 查找Canvas（View）
            for view in scene.views():
                if hasattr(view, 'on_node_deleted'):
                    view.on_node_deleted(self.node_id)
                    break
            
            # 从场景移除
            scene.removeItem(self)
    
    def set_executing(self, executing: bool):
        """设置执行状态"""
        self.is_executing = executing
        self.update()
    
    def set_error(self, error: bool):
        """设置错误状态"""
        self.is_error = error
        self.update()


class PortType:
    """端口类型"""
    INPUT = "input"
    OUTPUT = "output"


class PortGraphicsItem(QGraphicsEllipseItem):
    """端口图形项"""
    
    def __init__(self, parent_node: NodeGraphicsItem, port_type: str, position: QPointF, radius: float = 6):
        """
        初始化端口
        
        Args:
            parent_node: 父节点
            port_type: 端口类型（INPUT/OUTPUT）
            position: 相对于父节点的位置
            radius: 端口半径
        """
        super().__init__(
            position.x() - radius,
            position.y() - radius,
            radius * 2,
            radius * 2,
            parent_node
        )
        
        self.parent_node = parent_node
        self.port_type = port_type
        self.radius = radius
        
        # 样式
        self.setBrush(QBrush(QColor("#4CAF50")))
        self.setPen(QPen(QColor("#2d2d2d"), 2))
        
        # 连接线
        self.connections = []
    
    def get_scene_position(self) -> QPointF:
        """获取在场景中的位置"""
        return self.parentItem().scenePos() + self.rect().center()
    
    def add_connection(self, connection):
        """添加连接"""
        self.connections.append(connection)
    
    def remove_connection(self, connection):
        """移除连接"""
        if connection in self.connections:
            self.connections.remove(connection)


class ConnectionGraphicsItem(QGraphicsItem):
    """连接线图形项"""
    
    def __init__(self, start_port: PortGraphicsItem, end_port: PortGraphicsItem = None):
        """
        初始化连接线
        
        Args:
            start_port: 起始端口
            end_port: 结束端口
        """
        super().__init__()
        
        self.start_port = start_port
        self.end_port = end_port
        self.end_pos = None
        
        # 样式
        self.pen = QPen(QColor("#4CAF50"), 2)
        self.pen.setCapStyle(Qt.RoundCap)
        
        # 注册连接
        if self.start_port:
            self.start_port.add_connection(self)
        if self.end_port:
            self.end_port.add_connection(self)
        
        self.setZValue(-1)  # 放在节点下层
    
    def set_end_port(self, end_port: PortGraphicsItem):
        """设置结束端口"""
        if self.end_port:
            self.end_port.remove_connection(self)
        
        self.end_port = end_port
        
        if self.end_port:
            self.end_port.add_connection(self)
        
        self.update_path()
    
    def set_end_pos(self, pos: QPointF):
        """设置结束位置（用于拖动时）"""
        self.end_pos = pos
        self.update_path()
    
    def update_path(self):
        """更新路径"""
        self.prepareGeometryChange()
        self.update()
    
    def boundingRect(self) -> QRectF:
        """返回边界矩形"""
        if not self.start_port:
            return QRectF()
        
        start = self.start_port.get_scene_position()
        
        if self.end_port:
            end = self.end_port.get_scene_position()
        elif self.end_pos:
            end = self.end_pos
        else:
            end = start
        
        return QRectF(start, end).normalized().adjusted(-10, -10, 10, 10)
    
    def paint(self, painter: QPainter, option, widget=None):
        """绘制连接线"""
        if not self.start_port:
            return
        
        painter.setRenderHint(QPainter.Antialiasing)
        
        start = self.start_port.get_scene_position()
        
        if self.end_port:
            end = self.end_port.get_scene_position()
        elif self.end_pos:
            end = self.end_pos
        else:
            return
        
        # 绘制贝塞尔曲线
        painter.setPen(self.pen)
        
        # 计算控制点
        dx = abs(end.x() - start.x())
        offset = min(dx * 0.5, 100)
        
        ctrl1 = QPointF(start.x() + offset, start.y())
        ctrl2 = QPointF(end.x() - offset, end.y())
        
        # 绘制路径
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(start)
        path.cubicTo(ctrl1, ctrl2, end)
        
        painter.drawPath(path)
