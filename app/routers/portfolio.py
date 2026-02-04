from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List

from app.database import get_db
from app.core.security import verify_token
from app.models.portfolio import Portfolio
from app.services.stock_data import StockDataService
from app.core.config import settings
from app.schemas.portfolio import (
    AddPortfolioRequest,
    PortfolioResponse,
    UpdatePortfolioRequest,
    AngelOneConnectRequest,
    AngelOneSyncResponse,
    AngelOneHolding,
)
from app.services.angel_one import AngelOneService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/", response_model=PortfolioResponse)
@limiter.limit("30/minute")
async def get_portfolio(
    request: Request,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get user portfolio"""
    user_id = int(current_user['user_id'])
    
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    
    holdings = []
    for portfolio_item in portfolios:
        try:
            stock_info = StockDataService.get_stock_info(portfolio_item.symbol)
            current_value = stock_info['price'] * portfolio_item.shares
            cost_basis = portfolio_item.cost_basis * portfolio_item.shares
            gain = current_value - cost_basis
            
            holdings.append({
                "symbol": portfolio_item.symbol,
                "shares": portfolio_item.shares,
                "costBasis": cost_basis,
                "currentValue": current_value,
                "gain": gain,
            })
        except Exception as e:
            print(f"Error fetching stock {portfolio_item.symbol}: {e}")
            continue
    
    return PortfolioResponse(holdings=holdings)

@router.post("/add")
@limiter.limit("10/minute")
async def add_to_portfolio(
    request: Request,
    request_data: AddPortfolioRequest,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Add stock to portfolio"""
    user_id = int(current_user['user_id'])
    
    # Check if already exists
    existing = db.query(Portfolio).filter(
        Portfolio.user_id == user_id,
        Portfolio.symbol == request_data.symbol.upper()
    ).first()
    
    if existing:
        total_shares = existing.shares + request_data.shares
        new_cost_basis = ((existing.cost_basis * existing.shares) + (request_data.cost_basis * request_data.shares)) / total_shares
        
        existing.shares = total_shares
        existing.cost_basis = new_cost_basis
    else:
        new_portfolio = Portfolio(
            user_id=user_id,
            symbol=request_data.symbol.upper(),
            shares=request_data.shares,
            cost_basis=request_data.cost_basis
        )
        db.add(new_portfolio)
    
    db.commit()
    return {"message": "Stock added to portfolio"}

@router.delete("/{symbol}")
@limiter.limit("10/minute")
async def remove_from_portfolio(
    request: Request,
    symbol: str,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Remove stock from portfolio"""
    user_id = int(current_user['user_id'])
    
    portfolio_item = db.query(Portfolio).filter(
        Portfolio.user_id == user_id,
        Portfolio.symbol == symbol.upper()
    ).first()
    
    if not portfolio_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in portfolio"
        )
    
    db.delete(portfolio_item)
    db.commit()
    
    return {"message": "Stock removed from portfolio"}

@router.put("/{symbol}")
@limiter.limit("10/minute")
async def update_portfolio(
    request: Request,
    symbol: str,
    request_data: UpdatePortfolioRequest,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update a portfolio holding"""
    user_id = int(current_user['user_id'])
    portfolio_item = db.query(Portfolio).filter(
        Portfolio.user_id == user_id,
        Portfolio.symbol == symbol.upper()
    ).first()

    if not portfolio_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in portfolio"
        )

    if request_data.shares <= 0:
        db.delete(portfolio_item)
    else:
        portfolio_item.shares = request_data.shares
        portfolio_item.cost_basis = request_data.cost_basis

    db.commit()
    return {"message": "Portfolio updated"}

@router.post("/angel-one", response_model=AngelOneSyncResponse)
@limiter.limit("5/minute")
async def sync_angel_one(
    request: Request,
    request_data: AngelOneConnectRequest,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Fetch and optionally sync Angel One holdings"""
    user_id = int(current_user['user_id'])
    api_key = request_data.api_key or settings.ANGEL_ONE_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Angel One API key is required"
        )

    login_data = await AngelOneService.login(
        api_key=api_key,
        client_code=request_data.client_code,
        pin=request_data.pin,
        totp=request_data.totp,
        client_local_ip=request_data.client_local_ip,
        client_public_ip=request_data.client_public_ip,
        mac_address=request_data.mac_address,
    )

    if not login_data.get("status"):
        error_message = login_data.get("message", "Angel One login failed")
        error_code = login_data.get("errorcode") or login_data.get("errorCode")
        detail = f"{error_message} (code: {error_code})" if error_code else error_message
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

    token = (login_data.get("data") or {}).get("jwtToken")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Angel One token missing"
        )

    holdings_response = await AngelOneService.fetch_holdings(
        api_key=api_key,
        client_code=request_data.client_code,
        access_token=token,
        client_local_ip=request_data.client_local_ip,
        client_public_ip=request_data.client_public_ip,
        mac_address=request_data.mac_address,
    )

    if not holdings_response.get("status"):
        error_message = holdings_response.get("message", "Failed to fetch holdings")
        error_code = holdings_response.get("errorcode") or holdings_response.get("errorCode")
        detail = f"{error_message} (code: {error_code})" if error_code else error_message
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail
        )

    raw_holdings = (holdings_response.get("data") or {}).get("holdings") or []
    normalized: list[AngelOneHolding] = []
    for item in raw_holdings:
        symbol = (item.get("tradingsymbol") or item.get("symbol") or "").upper()
        quantity = float(item.get("quantity") or item.get("netqty") or 0)
        avg_price = float(item.get("averageprice") or item.get("avgprice") or item.get("averagePrice") or 0)
        if not symbol or quantity <= 0:
            continue
        normalized.append(AngelOneHolding(symbol=symbol, shares=quantity, averagePrice=avg_price))

    if request_data.sync:
        if request_data.replace:
            db.query(Portfolio).filter(Portfolio.user_id == user_id).delete()
            db.commit()

        for holding in normalized:
            existing = db.query(Portfolio).filter(
                Portfolio.user_id == user_id,
                Portfolio.symbol == holding.symbol
            ).first()
            if existing:
                existing.shares = holding.shares
                existing.cost_basis = holding.averagePrice
            else:
                db.add(Portfolio(
                    user_id=user_id,
                    symbol=holding.symbol,
                    shares=holding.shares,
                    cost_basis=holding.averagePrice
                ))
        db.commit()

    return AngelOneSyncResponse(synced=request_data.sync, holdings=normalized)
