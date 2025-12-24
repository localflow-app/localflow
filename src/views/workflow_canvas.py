import math
import time

from PySide6.QtCore import Qt, QLine, Signal, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QPainter
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView


class WorkflowCanvas(QGraphicsView):
    # 信号定义
    node_added = Signal(object)  # 节点被添加
    node_selected = Signal(object)  # 节点被选中
    node_deleted = Signal(str)  # 节点被删除 (node_id)
    connection_created = Signal(str, str)  # 连接被创建 (from_node_id, to_node_id)
    
    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.father = parent
        self._scene = scene
        self.setScene(self._scene)
        
        # Make the animation more smooth
        self.setRenderHint(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Hide the scrollbar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Always track the mouse when adjust the ratio
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        self._drag_mode = False
        
        # 连线模式
        self.connection_mode = False
        self.connection_start_port = None
        self.temp_connection = None
        
        # 启用拖放
        self.setAcceptDrops(True)
        
        # 设置焦点策略，确保可以接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event):
        # Zoom
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        # 检查是否点击在端口上
        item_at_pos = self.itemAt(event.pos())
        
        if event.button() == Qt.LeftButton:
            # 检查是否点击端口
            from src.views.node_graphics import PortGraphicsItem
            if isinstance(item_at_pos, PortGraphicsItem):
                self._start_connection(item_at_pos, event)
                return
            
            # 检查是否点击节点
            from src.views.node_graphics import NodeGraphicsItem
            if isinstance(item_at_pos, NodeGraphicsItem):
                # 如果点击的是已经选中的节点，不需要做额外处理
                # Qt会自动处理选中状态
                self.node_selected.emit(item_at_pos)
            else:
                # 点击空白区域，清除所有选中
                self._scene.clearSelection()
            
            self.leftButtonPressed(event)
        
        if event.button() == Qt.RightButton:
            self.right_click_add_node(f"# Node {str(int(time.time() * 1000))}", self.mapToScene(event.pos()))
        
        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.connection_mode and self.temp_connection:
            # 更新临时连接线的结束位置
            scene_pos = self.mapToScene(event.pos())
            self.temp_connection.set_end_pos(scene_pos)
        
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            # 检查是否在端口上释放（完成连接）
            if self.connection_mode:
                item_at_pos = self.itemAt(event.pos())
                from src.views.node_graphics import PortGraphicsItem, PortType
                
                if isinstance(item_at_pos, PortGraphicsItem):
                    self._finish_connection(item_at_pos)
                else:
                    self._cancel_connection()
            
            self.leftButtonReleased(event)
        
        self._drag_mode = None
        return super().mouseReleaseEvent(event)

    def leftButtonPressed(self, event):
        if self.itemAt(event.pos()) is not None:
            return
        else:
            # 点击空白区域时清除选中
            self._scene.clearSelection()
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self._drag_mode = True

    def leftButtonReleased(self, event):
        self.setDragMode(QGraphicsView.NoDrag)
        self._drag_mode = False
    
    def _start_connection(self, start_port, event):
        """开始创建连接"""
        from src.views.node_graphics import PortType, ConnectionGraphicsItem
        
        # 只能从输出端口开始连接
        if start_port.port_type != PortType.OUTPUT:
            return
        
        self.connection_mode = True
        self.connection_start_port = start_port
        
        # 创建临时连接线
        self.temp_connection = ConnectionGraphicsItem(start_port)
        self._scene.addItem(self.temp_connection)
        
        scene_pos = self.mapToScene(event.pos())
        self.temp_connection.set_end_pos(scene_pos)
    
    def _finish_connection(self, end_port):
        """完成连接"""
        from src.views.node_graphics import PortType
        
        # 只能连接到输入端口
        if end_port.port_type != PortType.INPUT:
            self._cancel_connection()
            return
        
        # 不能连接到同一个节点
        if end_port.parent_node == self.connection_start_port.parent_node:
            self._cancel_connection()
            return
        
        # 完成连接
        self.temp_connection.set_end_port(end_port)
        
        # 发射连接创建信号
        from_node_id = self.connection_start_port.parent_node.node_id
        to_node_id = end_port.parent_node.node_id
        self.connection_created.emit(from_node_id, to_node_id)
        
        # 重置状态
        self.connection_mode = False
        self.connection_start_port = None
        self.temp_connection = None
    
    def _cancel_connection(self):
        """取消连接"""
        if self.temp_connection:
            self._scene.removeItem(self.temp_connection)
        
        self.connection_mode = False
        self.connection_start_port = None
        self.temp_connection = None

    def right_click_add_node(self, node_text, pos):
        """右键添加节点"""
        from PySide6.QtWidgets import QMenu
        from src.core.node_base import NodeType
        from src.views.node_graphics import NodeGraphicsItem
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3f3f3f;
            }
            QMenu::item:selected {
                background-color: #0e639c;
            }
        """)
        
        # 添加节点类型选项
        var_assign_action = menu.addAction("变量赋值节点")
        var_calc_action = menu.addAction("变量计算节点")
        menu.addSeparator()
        sqlite_connect_action = menu.addAction("SQLite连接节点")
        sqlite_exec_action = menu.addAction("SQLite执行节点")
        sql_stmt_action = menu.addAction("SQL语句节点")
        
        # 获取鼠标点击位置（屏幕坐标）
        from PySide6.QtGui import QCursor
        action = menu.exec_(QCursor.pos())
        
        if action:
            # 确定节点类型
            node_type = None
            node_title = ""
            
            if action == var_assign_action:
                node_type = NodeType.VARIABLE_ASSIGN
                node_title = "变量赋值"
            elif action == var_calc_action:
                node_type = NodeType.VARIABLE_CALC
                node_title = "变量计算"
            elif action == sqlite_connect_action:
                node_type = NodeType.SQLITE_CONNECT
                node_title = "SQLite连接"
            elif action == sqlite_exec_action:
                node_type = NodeType.SQLITE_EXECUTE
                node_title = "SQLite执行"
            elif action == sql_stmt_action:
                node_type = NodeType.SQL_STATEMENT
                node_title = "SQL语句"
            
            if node_type:
                # 生成唯一ID
                import time
                node_id = f"node_{int(time.time() * 1000)}"
                
                # 创建节点图形项
                node_item = NodeGraphicsItem(node_id, node_type, node_title)
                node_item.setPos(pos)
                
                # 添加到场景
                self._scene.addItem(node_item)
                
                # 发射节点添加信号
                self.node_added.emit(node_item)
                
                print(f"添加节点: {node_title} ({node_id}) at {pos}")
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """放置事件"""
        if event.mimeData().hasText():
            node_type_str = event.mimeData().text()
            
            # 将字符串转换为NodeType枚举
            from src.core.node_base import NodeType
            node_type_map = {
                NodeType.VARIABLE_ASSIGN.value: (NodeType.VARIABLE_ASSIGN, "变量赋值"),
                NodeType.VARIABLE_CALC.value: (NodeType.VARIABLE_CALC, "变量计算"),
                NodeType.SQLITE_CONNECT.value: (NodeType.SQLITE_CONNECT, "SQLite连接"),
                NodeType.SQLITE_EXECUTE.value: (NodeType.SQLITE_EXECUTE, "SQLite执行"),
                NodeType.SQL_STATEMENT.value: (NodeType.SQL_STATEMENT, "SQL语句"),
            }
            
            if node_type_str in node_type_map:
                node_type, node_title = node_type_map[node_type_str]
                
                # 获取放置位置（场景坐标）
                scene_pos = self.mapToScene(event.pos())
                
                # 生成唯一ID
                import time
                node_id = f"node_{int(time.time() * 1000)}"
                
                # 创建节点图形项
                from src.views.node_graphics import NodeGraphicsItem
                node_item = NodeGraphicsItem(node_id, node_type, node_title)
                node_item.setPos(scene_pos)
                
                # 添加到场景
                self._scene.addItem(node_item)
                
                # 发射节点添加信号
                self.node_added.emit(node_item)
                
                print(f"拖拽添加节点: {node_title} ({node_id}) at {scene_pos}")
                
                event.acceptProposedAction()
    
    def keyPressEvent(self, event):
        """键盘按下事件"""
        from PySide6.QtCore import Qt
        from src.views.node_graphics import NodeGraphicsItem
        
        # 删除选中的节点（Del键或Backspace键）
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            selected_items = self._scene.selectedItems()
            for item in selected_items:
                if isinstance(item, NodeGraphicsItem):
                    item.delete_node()
        else:
            super().keyPressEvent(event)
    
    def on_node_deleted(self, node_id: str):
        """节点被删除的回调"""
        print(f"Canvas收到节点删除通知: {node_id}")
        self.node_deleted.emit(node_id)


class WorkflowGraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        scene_background_color = "#212121"
        scene_width = 32000
        scene_height = 32000
        # width
        scene_grid_size = 20
        # Determine how many small cells there are in the big cell
        scene_grid_chunk = 5
        # Drawing grid in the editor
        scene_grid_normal_line_color = "#313131"
        scene_grid_dark_line_color = "#131313"
        scene_grid_normal_line_width = 1.0
        scene_grid_dark_line_width = 1.0

        self.setBackgroundBrush(QBrush(QColor(scene_background_color)))
        self._width = scene_width
        self._height = scene_height
        # Center the scene
        self.setSceneRect(
            -self._width / 2, -self._height / 2, self._width, self._height
        )
        self._grid_size = scene_grid_size
        self._grid_chunk = scene_grid_chunk
        self._normal_line_pen = QPen(
            QColor(scene_grid_normal_line_color)
        )
        self._normal_line_pen.setWidthF(scene_grid_normal_line_width)

        self._dark_line_pen = QPen(QColor(scene_grid_dark_line_color))
        self._dark_line_pen.setWidthF(scene_grid_dark_line_width)

    def addItem(self, item):
        super().addItem(item)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)

        lines, dark_lines = self.cal_grid_lines(rect)
        painter.setPen(self._dark_line_pen)
        painter.drawLines(dark_lines)
        painter.setPen(self._normal_line_pen)
        painter.drawLines(lines)

    def cal_grid_lines(self, rect):
        left, right, top, bottom = (
            math.floor(rect.left()),
            math.floor(rect.right()),
            math.floor(rect.top()),
            math.floor(rect.bottom()),
        )

        # Top left corner
        first_left = left - (left % self._grid_size)
        first_top = top - (top % self._grid_size)

        # Calculate the start and end points of the lines
        lines = []
        dark_lines = []
        # Draw horizontal lines
        for v in range(first_top, bottom, self._grid_size):
            line = QLine(left, v, right, v)
            if v % (self._grid_size * self._grid_chunk) == 0:
                dark_lines.append(line)
            else:
                lines.append(line)
        # Draw vertical lines
        for h in range(first_left, right, self._grid_size):
            line = QLine(h, top, h, bottom)
            if h % (self._grid_size * self._grid_chunk) == 0:
                dark_lines.append(line)
            else:
                lines.append(line)

        return lines, dark_lines
    
    def keyPressEvent(self, event):
        """键盘按下事件"""
        from PySide6.QtCore import Qt
        from src.views.node_graphics import NodeGraphicsItem
        
        # 删除选中的节点（Del键或Backspace键）
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            selected_items = self.selectedItems()
            for item in selected_items:
                if isinstance(item, NodeGraphicsItem):
                    item.delete_node()
        else:
            super().keyPressEvent(event)