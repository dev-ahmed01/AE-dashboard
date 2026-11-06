"""Approved property design integration checks."""
import os
os.environ.setdefault('DATABASE_URL','sqlite:///:memory:')
os.environ.setdefault('JWT_SECRET','test-key-only-not-for-real-production-apps-123456')
import app

def test_template_files_present_and_valid():
    from pathlib import Path
    root=Path(app.__file__).parent
    assert (root/'property_template.html').exists()
    assert (root/'property_template.html').stat().st_size>10000
    from property_runtime import render_property
    assert callable(render_property)

def test_tenancy_schema_allows_multiple_contract_lengths():
    room=app.RoomInput(name='One Studio',tenancies=[
      {'weeks':51,'start':'Sep 2027','end':'Sep 2028','weekly':289,'illustrative':True},
      {'weeks':44,'start':'Sep 2027','end':'Jul 2028','weekly':305,'illustrative':True}
    ])
    assert len(room.tenancies)==2
    assert room.tenancies[0].illustrative is True
