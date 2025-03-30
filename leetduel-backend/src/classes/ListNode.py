class ListNode(object):
    def __init__(self, x=0, next=None):
        self.val = x
        self.next = next

    def __repr__(self):
        r = []
        copy = self
        while copy:
            r.append(copy.val)
            copy = copy.next

        return str(r)
    
def linkedList(a):
    if not a:
        return None
    
    head = curr = ListNode(a[0])
    for i in a[1:]:
        curr.next = ListNode(i)
        curr = curr.next

    return head