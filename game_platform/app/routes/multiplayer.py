from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.multiplayer import GameRoom, GameInvite
from models.game import Game
from models.user import User
from models import db
from datetime import datetime

multiplayer_bp = Blueprint('multiplayer', __name__)


@multiplayer_bp.route('/')
@login_required
def index():
    games = Game.query.filter_by(is_active=True).all()
    return render_template('multiplayer/index.html', games=games)


@multiplayer_bp.route('/api/rooms')
@login_required
def get_rooms():
    game_id = request.args.get('game_id', type=int)
    
    query = GameRoom.query.filter(GameRoom.status.in_(['waiting', 'playing']))
    if game_id:
        query = query.filter_by(game_id=game_id)
    
    rooms = query.order_by(GameRoom.created_at.desc()).all()
    
    room_list = []
    for room in rooms:
        room_list.append({
            'id': room.id,
            'game_id': room.game_id,
            'game_name': room.game.name if room.game else '',
            'room_name': room.room_name,
            'player1_id': room.player1_id,
            'player1_name': room.player1.nickname or room.player1.username if room.player1 else '等待中',
            'player2_id': room.player2_id,
            'player2_name': room.player2.nickname or room.player2.username if room.player2 else '等待中',
            'status': room.status,
            'created_at': room.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({'code': 200, 'data': room_list})


@multiplayer_bp.route('/api/create-room', methods=['POST'])
@login_required
def create_room():
    data = request.get_json()
    game_id = data.get('game_id')
    room_name = data.get('room_name', f'{current_user.nickname or current_user.username}的房间')
    
    if not game_id:
        return jsonify({'code': 400, 'msg': '请选择游戏'})
    
    game = Game.query.get(game_id)
    if not game:
        return jsonify({'code': 404, 'msg': '游戏不存在'})
    
    room = GameRoom(
        game_id=game_id,
        room_name=room_name,
        player1_id=current_user.id,
        status='waiting'
    )
    db.session.add(room)
    db.session.commit()
    
    return jsonify({
        'code': 200, 
        'msg': '房间创建成功', 
        'data': {
            'room_id': room.id,
            'game_id': room.game_id,
            'game_name': game.name,
            'room_name': room.room_name,
            'status': room.status
        }
    })


@multiplayer_bp.route('/api/join-room', methods=['POST'])
@login_required
def join_room():
    data = request.get_json()
    room_id = data.get('room_id')
    
    if not room_id:
        return jsonify({'code': 400, 'msg': '房间ID不能为空'})
    
    room = GameRoom.query.get(room_id)
    if not room:
        return jsonify({'code': 404, 'msg': '房间不存在'})
    
    if room.status != 'waiting':
        return jsonify({'code': 400, 'msg': '房间已开始或已结束'})
    
    if room.player1_id == current_user.id:
        return jsonify({'code': 400, 'msg': '不能加入自己的房间'})
    
    if room.player2_id:
        return jsonify({'code': 400, 'msg': '房间已满'})
    
    room.player2_id = current_user.id
    room.status = 'playing'
    room.updated_at = datetime.now()
    db.session.commit()
    
    return jsonify({
        'code': 200, 
        'msg': '加入房间成功', 
        'data': {
            'room_id': room.id,
            'game_id': room.game_id,
            'game_name': room.game.name,
            'room_name': room.room_name,
            'player1_id': room.player1_id,
            'player1_name': room.player1.nickname or room.player1.username,
            'player2_id': room.player2_id,
            'player2_name': room.player2.nickname or room.player2.username,
            'status': room.status
        }
    })


@multiplayer_bp.route('/api/leave-room', methods=['POST'])
@login_required
def leave_room():
    data = request.get_json()
    room_id = data.get('room_id')
    
    if not room_id:
        return jsonify({'code': 400, 'msg': '房间ID不能为空'})
    
    room = GameRoom.query.get(room_id)
    if not room:
        return jsonify({'code': 404, 'msg': '房间不存在'})
    
    if room.player1_id == current_user.id:
        if room.status == 'waiting':
            db.session.delete(room)
        else:
            room.status = 'finished'
            room.winner_id = room.player2_id
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已离开房间'})
    
    if room.player2_id == current_user.id:
        room.player2_id = None
        room.status = 'waiting'
        room.updated_at = datetime.now()
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已离开房间'})
    
    return jsonify({'code': 400, 'msg': '你不在这个房间里'})


@multiplayer_bp.route('/api/update-score', methods=['POST'])
@login_required
def update_score():
    data = request.get_json()
    room_id = data.get('room_id')
    score = data.get('score', 0)
    
    if not room_id:
        return jsonify({'code': 400, 'msg': '房间ID不能为空'})
    
    room = GameRoom.query.get(room_id)
    if not room:
        return jsonify({'code': 404, 'msg': '房间不存在'})
    
    if room.status != 'playing':
        return jsonify({'code': 400, 'msg': '游戏未在进行中'})
    
    if room.player1_id == current_user.id:
        room.player1_score = score
    elif room.player2_id == current_user.id:
        room.player2_score = score
    else:
        return jsonify({'code': 400, 'msg': '你不在这个房间里'})
    
    room.updated_at = datetime.now()
    db.session.commit()
    
    return jsonify({
        'code': 200, 
        'msg': '分数已更新',
        'data': {
            'player1_score': room.player1_score,
            'player2_score': room.player2_score
        }
    })


@multiplayer_bp.route('/api/end-game', methods=['POST'])
@login_required
def end_game():
    data = request.get_json()
    room_id = data.get('room_id')
    
    if not room_id:
        return jsonify({'code': 400, 'msg': '房间ID不能为空'})
    
    room = GameRoom.query.get(room_id)
    if not room:
        return jsonify({'code': 404, 'msg': '房间不存在'})
    
    if room.player1_id != current_user.id and room.player2_id != current_user.id:
        return jsonify({'code': 400, 'msg': '你不在这个房间里'})
    
    room.status = 'finished'
    
    if room.player1_score > room.player2_score:
        room.winner_id = room.player1_id
    elif room.player2_score > room.player1_score:
        room.winner_id = room.player2_id
    
    room.updated_at = datetime.now()
    db.session.commit()
    
    winner_name = ''
    if room.winner:
        winner_name = room.winner.nickname or room.winner.username
    
    return jsonify({
        'code': 200, 
        'msg': '游戏已结束',
        'data': {
            'winner_id': room.winner_id,
            'winner_name': winner_name,
            'player1_score': room.player1_score,
            'player2_score': room.player2_score
        }
    })


@multiplayer_bp.route('/api/invite', methods=['POST'])
@login_required
def invite():
    data = request.get_json()
    to_user_id = data.get('to_user_id')
    game_id = data.get('game_id')
    
    if not to_user_id or not game_id:
        return jsonify({'code': 400, 'msg': '参数不完整'})
    
    if to_user_id == current_user.id:
        return jsonify({'code': 400, 'msg': '不能邀请自己'})
    
    to_user = User.query.get(to_user_id)
    if not to_user:
        return jsonify({'code': 404, 'msg': '用户不存在'})
    
    game = Game.query.get(game_id)
    if not game:
        return jsonify({'code': 404, 'msg': '游戏不存在'})
    
    invite = GameInvite(
        from_user_id=current_user.id,
        to_user_id=to_user_id,
        game_id=game_id,
        status='pending'
    )
    db.session.add(invite)
    db.session.commit()
    
    return jsonify({
        'code': 200, 
        'msg': f'已向 {to_user.nickname or to_user.username} 发送游戏邀请'
    })


@multiplayer_bp.route('/api/respond-invite', methods=['POST'])
@login_required
def respond_invite():
    data = request.get_json()
    invite_id = data.get('invite_id')
    action = data.get('action')  # 'accept' or 'reject'
    
    if not invite_id or not action:
        return jsonify({'code': 400, 'msg': '参数不完整'})
    
    invite = GameInvite.query.get(invite_id)
    if not invite:
        return jsonify({'code': 404, 'msg': '邀请不存在'})
    
    if invite.to_user_id != current_user.id:
        return jsonify({'code': 400, 'msg': '这不是你的邀请'})
    
    if invite.status != 'pending':
        return jsonify({'code': 400, 'msg': '邀请已处理'})
    
    if action == 'accept':
        invite.status = 'accepted'
        room = GameRoom(
            game_id=invite.game_id,
            room_name=f'{current_user.nickname or current_user.username}的邀请房间',
            player1_id=invite.from_user_id,
            player2_id=invite.to_user_id,
            status='playing'
        )
        db.session.add(room)
        db.session.commit()
        
        return jsonify({
            'code': 200, 
            'msg': '已接受邀请',
            'data': {
                'room_id': room.id,
                'game_id': room.game_id
            }
        })
    elif action == 'reject':
        invite.status = 'rejected'
        db.session.commit()
        return jsonify({'code': 200, 'msg': '已拒绝邀请'})
    
    return jsonify({'code': 400, 'msg': '无效的操作'})


@multiplayer_bp.route('/api/my-invites')
@login_required
def my_invites():
    invites = GameInvite.query.filter_by(to_user_id=current_user.id).order_by(GameInvite.created_at.desc()).limit(20).all()
    
    invite_list = []
    for invite in invites:
        invite_list.append({
            'id': invite.id,
            'from_user_id': invite.from_user_id,
            'from_user_name': invite.from_user.nickname or invite.from_user.username,
            'game_id': invite.game_id,
            'game_name': invite.game.name if invite.game else '',
            'status': invite.status,
            'created_at': invite.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({'code': 200, 'data': invite_list})


@multiplayer_bp.route('/api/room/<int:room_id>')
@login_required
def get_room(room_id):
    room = GameRoom.query.get(room_id)
    if not room:
        return jsonify({'code': 404, 'msg': '房间不存在'})
    
    return jsonify({
        'code': 200,
        'data': {
            'id': room.id,
            'game_id': room.game_id,
            'game_name': room.game.name if room.game else '',
            'room_name': room.room_name,
            'player1_id': room.player1_id,
            'player1_name': room.player1.nickname or room.player1.username if room.player1 else '',
            'player1_score': room.player1_score,
            'player2_id': room.player2_id,
            'player2_name': room.player2.nickname or room.player2.username if room.player2 else '',
            'player2_score': room.player2_score,
            'status': room.status,
            'winner_id': room.winner_id
        }
    })
