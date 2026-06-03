from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.friend import Friend
from models import db
from sqlalchemy import or_

friend_bp = Blueprint('friend', __name__)

@friend_bp.route('/')
@login_required
def index():
    return render_template('friend/index.html')

@friend_bp.route('/api/list')
@login_required
def list_friends():
    """获取好友列表（包括已接受的好友）"""
    friendships = Friend.query.filter(
        or_(
            (Friend.user_id == current_user.id),
            (Friend.friend_id == current_user.id)
        ),
        Friend.status == Friend.ACCEPTED
    ).all()
    
    friends = []
    for f in friendships:
        if f.user_id == current_user.id:
            friend_user = f.friend
        else:
            friend_user = f.user
        friends.append({
            'id': f.id,
            'friend_id': friend_user.id,
            'username': friend_user.username,
            'nickname': friend_user.nickname,
            'avatar': friend_user.avatar,
            'total_score': friend_user.total_score
        })
    
    return jsonify({'success': True, 'friends': friends})

@friend_bp.route('/api/requests')
@login_required
def list_requests():
    """获取收到的待处理好友请求"""
    requests = Friend.query.filter(
        Friend.friend_id == current_user.id,
        Friend.status == Friend.PENDING
    ).all()
    
    request_list = []
    for f in requests:
        request_list.append({
            'id': f.id,
            'user_id': f.user_id,
            'username': f.user.username,
            'nickname': f.user.nickname,
            'avatar': f.user.avatar,
            'created_at': f.created_at.isoformat() if f.created_at else None
        })
    
    return jsonify({'success': True, 'requests': request_list})

@friend_bp.route('/api/send', methods=['POST'])
@login_required
def send_request():
    """发送好友请求"""
    friend_id = request.json.get('friend_id') if request.is_json else request.form.get('friend_id')
    
    if not friend_id:
        return jsonify({'success': False, 'message': '请选择要添加的好友'})
    
    friend_id = int(friend_id)
    
    if friend_id == current_user.id:
        return jsonify({'success': False, 'message': '不能添加自己为好友'})
    
    friend_user = User.query.get(friend_id)
    if not friend_user:
        return jsonify({'success': False, 'message': '用户不存在'})
    
    # 检查是否已经是好友或已发送请求
    existing = Friend.query.filter(
        or_(
            (Friend.user_id == current_user.id) & (Friend.friend_id == friend_id),
            (Friend.user_id == friend_id) & (Friend.friend_id == current_user.id)
        )
    ).first()
    
    if existing:
        if existing.status == Friend.ACCEPTED:
            return jsonify({'success': False, 'message': '你们已经是好友了'})
        elif existing.status == Friend.PENDING:
            if existing.user_id == current_user.id:
                return jsonify({'success': False, 'message': '已发送过好友请求，请等待对方确认'})
            else:
                return jsonify({'success': False, 'message': '对方已发送过好友请求，请去处理'})
        else:
            # 被拒绝或已删除，重新创建
            existing.status = Friend.PENDING
            existing.user_id = current_user.id
            existing.friend_id = friend_id
            existing.created_at = db.func.now()
            db.session.commit()
            return jsonify({'success': True, 'message': '好友请求已发送'})
    
    new_friend = Friend(user_id=current_user.id, friend_id=friend_id, status=Friend.PENDING)
    db.session.add(new_friend)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '好友请求已发送'})

@friend_bp.route('/api/accept', methods=['POST'])
@login_required
def accept_request():
    """接受好友请求"""
    request_id = request.json.get('request_id') if request.is_json else request.form.get('request_id')
    
    if not request_id:
        return jsonify({'success': False, 'message': '请求ID不能为空'})
    
    request_id = int(request_id)
    
    friend_request = Friend.query.get(request_id)
    
    if not friend_request:
        return jsonify({'success': False, 'message': '请求不存在'})
    
    if friend_request.friend_id != current_user.id:
        return jsonify({'success': False, 'message': '无权操作此请求'})
    
    if friend_request.status != Friend.PENDING:
        return jsonify({'success': False, 'message': '请求已被处理'})
    
    friend_request.status = Friend.ACCEPTED
    db.session.commit()
    
    return jsonify({'success': True, 'message': '已接受好友请求'})

@friend_bp.route('/api/reject', methods=['POST'])
@login_required
def reject_request():
    """拒绝好友请求"""
    request_id = request.json.get('request_id') if request.is_json else request.form.get('request_id')
    
    if not request_id:
        return jsonify({'success': False, 'message': '请求ID不能为空'})
    
    request_id = int(request_id)
    
    friend_request = Friend.query.get(request_id)
    
    if not friend_request:
        return jsonify({'success': False, 'message': '请求不存在'})
    
    if friend_request.friend_id != current_user.id:
        return jsonify({'success': False, 'message': '无权操作此请求'})
    
    if friend_request.status != Friend.PENDING:
        return jsonify({'success': False, 'message': '请求已被处理'})
    
    friend_request.status = Friend.REJECTED
    db.session.commit()
    
    return jsonify({'success': True, 'message': '已拒绝好友请求'})

@friend_bp.route('/api/delete', methods=['POST', 'DELETE'])
@login_required
def delete_friend():
    """删除好友"""
    friend_id = request.json.get('friend_id') if request.is_json else request.form.get('friend_id')
    
    if not friend_id:
        return jsonify({'success': False, 'message': '请选择要删除的好友'})
    
    friend_id = int(friend_id)
    
    friendship = Friend.query.filter(
        or_(
            (Friend.user_id == current_user.id) & (Friend.friend_id == friend_id),
            (Friend.user_id == friend_id) & (Friend.friend_id == current_user.id)
        ),
        Friend.status == Friend.ACCEPTED
    ).first()
    
    if not friendship:
        return jsonify({'success': False, 'message': '好友关系不存在'})
    
    db.session.delete(friendship)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '已删除好友'})

@friend_bp.route('/api/friend-scores')
@login_required
def friend_scores():
    """获取好友分数排行榜"""
    friendships = Friend.query.filter(
        or_(
            (Friend.user_id == current_user.id),
            (Friend.friend_id == current_user.id)
        ),
        Friend.status == Friend.ACCEPTED
    ).all()
    
    friend_ids = []
    for f in friendships:
        if f.user_id == current_user.id:
            friend_ids.append(f.friend_id)
        else:
            friend_ids.append(f.user_id)
    
    if not friend_ids:
        return jsonify({'success': True, 'rankings': []})
    
    friends = User.query.filter(User.id.in_(friend_ids)).order_by(User.total_score.desc()).all()
    
    rankings = []
    for i, friend in enumerate(friends, 1):
        rankings.append({
            'rank': i,
            'user_id': friend.id,
            'username': friend.username,
            'nickname': friend.nickname,
            'avatar': friend.avatar,
            'total_score': friend.total_score
        })
    
    return jsonify({'success': True, 'rankings': rankings})

@friend_bp.route('/api/search')
@login_required
def search_users():
    """搜索用户"""
    keyword = request.args.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({'success': True, 'users': []})
    
    users = User.query.filter(
        or_(
            User.username.like(f'%{keyword}%'),
            User.nickname.like(f'%{keyword}%')
        )
    ).limit(20).all()
    
    # 排除自己
    users = [u for u in users if u.id != current_user.id]
    
    user_list = []
    for u in users:
        # 检查是否已经是好友或有待处理的请求
        existing = Friend.query.filter(
            or_(
                (Friend.user_id == current_user.id) & (Friend.friend_id == u.id),
                (Friend.user_id == u.id) & (Friend.friend_id == current_user.id)
            )
        ).first()
        
        status = 'none'
        if existing:
            if existing.status == Friend.ACCEPTED:
                status = 'friends'
            elif existing.status == Friend.PENDING:
                if existing.user_id == current_user.id:
                    status = 'pending_sent'
                else:
                    status = 'pending_received'
            else:
                status = 'none'
        
        user_list.append({
            'id': u.id,
            'username': u.username,
            'nickname': u.nickname,
            'avatar': u.avatar,
            'total_score': u.total_score,
            'friend_status': status
        })
    
    return jsonify({'success': True, 'users': user_list})
