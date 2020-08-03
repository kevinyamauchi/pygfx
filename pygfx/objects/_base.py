from ..linalg import Vector3, Matrix4, Quaternion


class WorldObject:
    """ The base class for objects present in the "world", i.e. the scene graph.

    Each WorldObject has geometry to define it's data, and material to define
    its apearance. The object itself is only responsible for defining object
    hierarchies (parent / children) and its position and orientation in the world.

    This is considered a base class. Use Group to collect multiple world objects
    into a single empty world object.
    """

    _v = Vector3()
    _m = Matrix4()
    _q = Quaternion()

    def __init__(self):
        self.parent = None
        self._children = []

        self.position = Vector3()
        self.rotation = Quaternion()
        self.scale = Vector3(1, 1, 1)

        self.up = Vector3(0, 1, 0)

        self.matrix = Matrix4()
        self.matrix_world = Matrix4()
        self.matrix_world_dirty = True

        self.visible = True
        self.render_order = 0

    @property
    def children(self):
        return tuple(self._children)

    def add(self, obj):
        # orphan if needed
        if obj.parent is not None:
            obj.parent.remove(obj)
        # attach to scene graph
        obj.parent = self
        self._children.append(obj)
        # flag world matrix as dirty
        obj.matrix_world_dirty = True
        return self

    def remove(self, obj):
        if obj in self._children:
            obj.parent = None
            self._children.remove(obj)

    def traverse(self, callback):
        callback(self)
        for child in self.children:
            child.traverse(callback)

    def update_matrix(self):
        self.matrix.compose(self.position, self.rotation, self.scale)
        self.matrix_world_dirty = True

    def update_matrix_world(
        self, force=False, update_children=True, update_parents=False
    ):
        if update_parents and self.parent:
            self.parent.update_matrix_world(
                force=force, update_children=False, update_parents=True
            )
        self.update_matrix()
        if self.matrix_world_dirty or force:
            if self.parent is None:
                self.matrix_world.copy(self.matrix)
            else:
                self.matrix_world.multiply_matrices(
                    self.parent.matrix_world, self.matrix
                )
            self.matrix_world_dirty = False
            for child in self._children:
                child.matrix_world_dirty = True
        if update_children:
            for child in self._children:
                child.update_matrix_world()

    def look_at(self, target: Vector3):
        self.update_matrix_world(update_parents=True, update_children=False)
        self._v.set_from_matrix_position(self.matrix_world)
        self._m.look_at(self._v, target, self.up)
        self.rotation.set_from_rotation_matrix(self._m)
        if self.parent:
            self._m.extract_rotation(self.parent.matrix_world)
            self._q.set_from_rotation_matrix(self._m)
            self.rotation.premultiply(self._q.inverse())