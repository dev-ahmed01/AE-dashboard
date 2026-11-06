"""Opt-in local example listing. Never seeds production or publishes demo rates."""
from sqlalchemy import select

def seed_kingston(db, Property, Room):
    if db.scalar(select(Property.id).where(Property.slug=="iq-kingston")):
        return
    root="/accom-template/assets/"
    gallery=[{"url":root+photo+".webp","alt":"Illustrative "+label+" - not a photograph of iQ Kingston",
        "category":label,"layout":"large" if i==0 else "regular"}
        for i,(photo,label) in enumerate([("ensuite","En suite bedroom"),("lounge","Shared lounge"),
        ("studio","Studio"),("study","Study spaces")])]
    prop=Property(name="iQ Kingston",slug="iq-kingston",city="Kingston upon Thames",
        country="United Kingdom",address="15 Wood Street, Kingston upon Thames",postcode="KT1 1TY",
        university="Kingston University",is_demo=True,noindex=True,published=False,
        seo_title="iQ Kingston · Demonstration | Accom by Emlen",
        meta_description="Demonstration student accommodation page with illustrative photos, rooms and rates.",
        description="Modern en suite and studio student accommodation near Kingston University, with social, study and leisure areas. The images, rates and tenancy dates shown on this demo page are illustrative and must not be treated as verified availability.",
        highlights=["Close to Kingston University","En suite and studio options",
        "Shared study and social spaces","Check current provider terms"],
        amenities=["Wi-Fi (verify contract)","Communal study areas","Gym","Cinema room",
        "Laundry (additional charges may apply)"],gallery=gallery,
        policies=[{"question":"Cancellation and visa conditions","answer":"Request the current operator agreement before committing to a booking."},
        {"question":"Visitors and overnight guests","answer":"Confirm the current visitor policy with the accommodation provider."}],
        faq=[{"question":"Are bills included?","answer":"The operator advertises selected inclusive bills. Verify the full agreement before paying."},
        {"question":"What happens after I enquire?","answer":"Accom can follow up with guidance; the provider handles payment and confirmed bookings."}],
        landmarks=[{"name":"Kingston University","detail":"Walkable distance; check the latest route"},
        {"name":"Kingston College","detail":"Nearby campus"}])
    db.add(prop)
    db.flush()
    examples=[("Bronze Ensuite","En suite",13,"Shared kitchen","Private bathroom","ensuite",[(51,289),(44,305)]),
      ("Silver Ensuite","En suite",15,"Shared kitchen","Private bathroom","ensuite",[(51,315),(44,329)]),
      ("Bronze Studio","Studio",18,"Private kitchenette","Private bathroom","studio",[(51,365),(44,389)])]
    for name,kind,size,kitchen,bathroom,photo,options in examples:
        db.add(Room(property_id=prop.id,name=name,room_type=kind,size_sqm=size,
            kitchen=kitchen,bathroom=bathroom,image_url=root+photo+".webp",
            image_alt="Illustrative "+name+" interior",price=None,availability="enquire",
            active=True,details="Specifications and availability to be confirmed with provider.",
            tenancies=[{"weeks":weeks,"start":"12 Sep 2027","end":"2028 (confirm)",
                "weekly":amount,"availability":"Request availability","illustrative":True}
                for weeks,amount in options]))
    db.commit()
