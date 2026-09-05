"""Behavior clone of a public elite action calendar."""
import base64
import json
import zlib
from collections import Counter
from pathlib import Path
from typing import Any
MODEL_PAYLOAD: str | None = 'eNrtXV1vXFdy/C985oNnhqTpvMnybCysbAn62MHGIAwD2SBAsHlw8hbkv0cSOXfuvae6qrrPGYrO8kmDGere8326q6urf/mfi3/77fe//+33i3/65eLti/fvL+4uL/79t//81//69MWnj3//7ff/+Nt/f/78v5fzP/3+46vXP/z66T98+PhuH/2fXy5+fPXlV/rh+49//fXFz69+evH64vLi5ZvDxeXG/fr9j/v9W+eH9/v9D5++/mn/+s3PF5fXq68PP+5ffLi4vL1bdfLtq5d//vh29vqpl+C32Vfzt8Mvf37z7sOPF3fLsfrcoLfv3vzw8eWHU5uuoqFYN/X1i5f7h18X7Tzs33+4mL1z8Wk1i0Z7NuEYTX9gvx2Mwurhf/o8P4sHrtcdfvL9a8mDX75Yrtr1ALYPS83aJrOS9i/IGMme8PE/PehT/37+MG0B1a/VS46PgU8+vPiwf7dq9uptrP3Rwm1nemow6Mt9G1JLaXrc6cPUk8ICev/m43rBrL+qrJzjM+jItAMyLarETJgr6TRKs/7J8X8YFPjE03OOq+H+sJz9lprZY5/vOzIfhdM37Vp9+C016bMVM31q3wVGx53+h3lEy7YZfWu0+Cw7I9dsQz1w4PxAI7feiLknPlgvs7U/W1dffsstouZxYHDUY8E9c3wsmr72efYFszLdZi9q99TpJ9X+9WrZdlt6S5Pr6k4eE6AJcBXPt/TLN69f719++PVP+3cfXr1+9S/5xQQMl9V9kVpMD9/gOz7Z2nZNPXyjnmld9fA/ooGZupSwI9rTbHrK1IfC8dKO9/S0YBysM1qf/lNTjxsqYUG0O7Z93Om5+afNLrgRj4sOv8v2SMt1enX4XS5PLnMFsOOv7b2c6tTj9CH6/LTnp/1hn8YvhKUR8H7/+jNEMfvTy+s7ddnW7IjGJFqDOu8/vHtx+H7/7t1fP9sMhvm4MimuE7AFMm02xjupWSAPafDA9hY12q2ty+MhDa+XioXUmnmhOWEZFu3zgE1EmmcPRPsebGAgUKTSDeQkJ4wMMHGngQZ+vG4iwCOmoZ48pca5G7To5GCvneNcRxgipB8I2ssxIWmGgCZOs3d6zunT/fgXJw8tB9Bp2yF9sN1mx7AzlQsoqH2A0UcwDdTnrhitkYU6v1iTXl37khggqBkB09IZYlJM6+brmzsdGIVjsABoCEES8Ho1bZdm9xBfc+bXERCksmVt15+DC9WIQmsB9CAu4P4fYgoB9EVdSieMQxwJdSsEwkqrERjzJnDH8wHIHdWhtVY0iIG1k7BSgQXSGNjMGqsPc/j4qikCDJCEq8GMpdqlSrq8hu2rthIKWfnXChpDhlU9Iwb/gE8bGh4ZaIyI+IgRBogNkLHQgjI6yPXdbWhUQhgMdEGYg+3/bvVUBxdtdP/a91xusuvXnJprdFkzJCExNWNRoB5kQvfjxxfv/mJZeMwiCLHQtKdOJqPfyjv1dX7vT99aPdoa5lTDzljBCvwPUnbMvEunx4Jvi50D+EbQp3UkFf6eXYh8OaiVqOCiI5CCziK8VtRgRscrhetaXEcszgy4qDlDuScDe7mPmQXsXMZR0S184jbW6fuHd+y257G7oivn0+x/erq8lZMxl/A6iwNlV2VMyDIUajhGFV4gNJw48FYj3nRZfrvsoOfswAmxcQ6udkpADCMzxVYAil/KRZNP3MMpmhLgaK9Zhv306fIogEGeWgfwOr3ShQV6emaX3wTa6D+PWpWAAVoi/bAQ1GJIZVSKEZ8AU6uLonQirI6ARUIeWV/EbDWmQ549Jk72OMaKZ4hsJACUN4E6c7LWqVSa8bwak93CUDo93EhQspkyLsZimzdGkk4ZovLMIJfbi1uWjEYT02mdKAXdMzoizhVMbC1hY6P4BhgQeWIXjbAWUwQGFDr7KyGTONg3m6jDmzefdvENdRuaP7++g8fV/Y8bBxEDJvb6vrwchSrvOvNI2Ql3c+cYR9P4tyfWmp8TzAOxJVRu6LLBu7uE6YVoRCDzLgxC+nzImwjyOSatYe46SLONMxkhR276JLNdRYMJ8nZqC8+LRMPN+FsWkgVyxOY+xeK0RksQ5fPt0+mD7ZUBFhkx+Wtphe09cbJ+26UDeg/aFmVTpjxGkpJJXtR+g5Z0oTnxigiTafGBXUgsbVcGvRLBbgaTVFkaM6C0XRu0TS0evBqQ3GQALhdJUA39zVyKTIywQ0rIjL70YODIJVFCKkLDEgwAt4vTufKdTMEr4K/lceMrZNPu7jr8ugDb3dUA5h4P5KsRAsblERiQcfVlLG0xxJOHS1PYhMaK27newx3+Fr8z0OAkAE9n3pnJ0pe53k57jNqmfFg7XcWnL8TeXK7Plk24unr8QSbzSe/VmmPOpnR+vSHgExk5dTICCQTQRI+a8c24VTK/AxgSNPGkOTxPS4MTfuTAg3Wg399adZKGBcYYSVUk0t7hEFAnh2T5FMMO0+uWmxWQEsbETVgievxTzJHozVYHX4EAzHky2Vn3zpLl/lWiIl8tAtIYT9/mox03Ph23YmOdlYbZ2cKywglHWGlIgRlKnFhopTR+cVB/evX6z18m1vZKKATMbORpRxzfWbBbW+hn6gA25+L/QJq22cYijF0WMBRQBIbpynp0Jvjm2GTIv+rlXzP400vm9kQtl+TeBpK4LfLKIticGkykGxYikT+Z5kgYlo6jgTcFtl9psB0Y1u3inR/8YSqaz2a9MWQClT16Gh6QVB5jwOnwBNjALi2WyVlknAWL1dZ+QLhoPdmRSF60CyLWeFy5MdDI33foADiaBb5cQDbXgEArjJONPvX7zoDzbYcsEmAFUUVTzH4ax01OzOL05OcbmRM2FL4XlKWhUq92vORGopMkYD2A1yog8BjXerwoyXetSXKtL1WoxtSGTob6fpoSQqnyZBuf9jOjvUnXamzmZS78oBPzH11hoeSKmty4sVqZzgdlroFt35v2yscHnzOd+HC7xHg+GXU1KnEHbcntw3AEPu1nrLkr4cUf/6qkDEcaBloRDyFt2WW2DsGln2jK5DSALcxyLlz0JGABx42+uavi/MCAplE80Cu7B4ZMuFznMhG2hkr2WLuWxjwbuqrwG1iG+xi8SQxHh4CaFcv74dU/u6wcMUgd9QiAgawyZ8J5Sy4mdqRY0U0ZgR0p6kNvFC86mHDymQ8VP9D1JbtTixlR2hyf4RCQ91VBmcrTTzrrAJACKAhNXUqF4zDu8ifHpWzK3xTl8rCruZHVia4emYq3+lBIUD54rv6gKkjAPCdhtezrv07+M21uZ+qWSJSlCT9eu/pE79pXiEhpTbeYQAkUuWcnUAu5PpJcI9FFVnSeR6a9HohyzqXKhy6JvwCNTnot4Rz8jN70IUcE+OHdm7d2pk1MCDiGto8pYLZwK4I81IJrL1RmxCfgD+ZCJGJbdADXA87HMZGngiyf+XKqjlFMBsikrTBflI6XENdepRMY55kb+mroHLvF9KVHUUytHcqXOAS1irEmFF2Lp86bC4EcQV4IcBpkk4rKBvo6x/7YdDAFmiSjcIr4rjXUwUrbkQe6hGwYOv/u50neBGqEWZlAykmhLjGrL7gvH3Jqm84HLz5VvBg1CRaXlshVSa0a3LuMiEFRP3Z27765G+YFD/mQCPOa6madX27QlzeWSZKflRnn0UUZbmyYgTjynoKIFe7pVLJ3fKMGBwdNbEv25fzIpLJDOaWp6UsyvH0udINdZKov/ZHwZZZGWl257nf7gXe28t2UP8oGXh7U2+/qOsXtWmnTBdtv6hmkQ2xWcZ+jaqINKxvOyL6n/NONXdJe82RUaQoVymOxM49wrvREiSjAcoeG2nhqEgbF/24yoebTq6bApCF5JLc1ZzC4yym0vpitarBtE4mdPJoD97taSAdLp5G6qS55cuz2RjLBeCTZAeqObWHkyyct4K9TP8SHS8mGya0aqiLNxwq700QgxUFyUtk6pqg9vjwUSp3Y1/7olCrqbTMFTdtTOYELCqZELIcTP4fO78r+uu2UZjehwhEx9Z7TLWaXmCSUbAcpspxs8d7gQkJNQZ0eMGbAKb/DHO+9zM6z+pQb95z0Lv2KFZB3pHHzttQQTf5+LKud/MfAr2JQS3m41PF1KDG+oKWXkWFZCMl0BpYxIFgIlSz3jAvc2mVt31onH4TPuDxTEpzMxKQYoUz6x+04GHXDBUtjUEwHcEmVpExV0qiAiVEj+zqBr556Z6d1SdSM5lFUS4/elBWzZ11UtAKANmOLmoAwfQsR0DZoFjA4CqhkG0c6eIq1OqlZ2ynvLFSwxrsBjUNMcBh0zuVYq0CrDVVZYNkyTAZjSt+JM2huawFicY+cQhlYYol6QDSP6zxnQGs1B0puasNTS3wMr+BQ5W9Gk2G6FtzGqWx6yRDINtop/NfN6oAaZhTZtvMTqNkZSS0Mh6IYQNiRfeFJtYhZ0mXPxPQwUQYHD9DUor1KGRqFz6ClDcxRvj8wghurZwMphCGLDvSvNZ4YjS1ucgj6kShtNzptHW745nCVEWJq7KMggAzXZLE8GpId3AE3iKd8GdAfsNNK8TCrdhtjGBg5xpdE9GlwbPIfkxkWI2t25N7GXpaaHpcrX2V77jKiRGfaqF/kAzUdqzNX95IgaVnmQkebbZoYaDiDxxg7If5qEDgG3KYiM0ztHp+D4lzwBjLm8W395U5lJMbcjzYSliV8Ulc3Qmd6qBhJsRi6G7xeiBkoeL9sr0plbisU4Wm7+ScUkC6obVarH3QSCkWkUxGJ4FyJ0CGnmIOZh6/Xkg9mkQGnmaIcxDrP0HPNWSQBWgF9z974BGxYgN17lk12zDV0Swf4EcecH9z7RN02/t1YUnC+2h7rFNNu9sd9k6nEKG79OLBh6sUY+N/VLuFN0yxXQHzcWwzIIVRfOszxXCcCq4hzo+Vpx/OWKX+NK9GbG77gjG0VoLAJyndTE4V2tX2GKRTdbAEjqRBU3YhKrtvNjQuLPANKj/rlzRhnuqZrFGUcpoKW/AAgB+EctY0+F6yP7V2fYk2RmgWKXYCK2HaB9BUuuODQnR63YjZfJzR3oSBHjES5x3w7u6MwQFH//Py0LX6r+ffVVU9SfDszqW1kTt56fSt2jUpFpw5AbmZAa0Fi/d7K3KkoTYF9jrkklTPiOgS5MWCR0Vlvt9Rs72BnkaVlZ2iBZq7pssDPdXPkXZeUUgD3sY1IU4qZGP3z0YDAekljEtydEHpUszUuOGYAXuRoGlhSrUsz/RSQtALnqjQjUICMhiIIr6FdalYm+fClxK9tecR2ZcxXyKWUR8L4CZyC6u2BzqB6BBX5sveK16OoilqcfFk7qSrgFB2IAXzqKPJ4s/y4/BLSNoolgV0xG5khk+LXYmVfMW6zhWqPikR5StUOJ1dGcfSp5NH1WWTelwADwz2eP03zWwERCtKlVLzGy5g1wveOBASy6ZgkPUwpvi9AtabjMEySAXrNg/6guY3A43lSgNmGnmVyajbf2AwrhLAYQEWVYeWhZ0MIVkrvOkW3ytcEG9EHX/hWAUdtb2nXyJT0WCdWDKnKvnKq3mQL+ERcq/b8aOEZmyCjOmRa/UPJiG3QEeyOfL2tvNUyaLf7DDjWYS7QlQOAQu/Qlb/3i24xTUHBBhqrRcQNWWwTSgjOUiE6Hw2LmVJCOBf87CL1uSXVJGeKOcGmvSKc0XOqVnnAmQkYAlgY6rO+71KyaUI9js7Fl9d9u0ov6oQkmJaxqc3vUnqKXnCgmZHBhS2BHlfvjipTjVqBbvTMLEzlaCrR/b/pyC2WZEqbhPmYYkSmQtjSOW51VnKZo7poey2kQOqVW+RBXuGsj5/s7W9owpisV9RURrctFoG4vguqqB8BHbOAuocxnWEmMvCXpM6yOpvm6VvS6QJp3GRg+d3lMBcGDfYzE6wL2Mo59u1zJf51GyvSL49ookZ/qa9VWgmZZi9Q3zLBbykc3csB2JVC9ix1smUpS47ILtG7Nmhfx57cCHKpaG9S27onfj9fJC0eK5eTnf5bFfHaJO5aEPQwq0HZ5fi4vFXmXg0GjKtrqUh3sh63XuZpPRSoMRKr9EULrNLW6UWz0kDEqZ//GfoO2GSHuKl21aiGE/jwzo2jussK49DE0HSFB6ahmqjfjY5JUAhE0Wz42XP6O6dgVCbY3kRD5wsEjDNfZTqJSRH/HpaKh/tCbli7XHwaKbt5XcbvahvIQPY0tIQaA5m+JqqA5mkqD1eaCz+PGKSTiYp65nHmBVesCptr8DFrUwAOIOf/RgTHAEd1ifV+uQ9uxSEfnObfh1Ob2Re4NsN69EA+BsMK5cYH4jr7vKjkcgVdpaovUS5/AnZPhISyzP5ymFQXmRJ3tTgiKASmKJ158MWkbljyWhyYSVi0bHExzTy/6u1ynUV5Au0bKukIPIYftyrL02S8gGc06xHQrD7RrM229S5ubFIXEKPfXA+vr0gcDsY7P5tulpXmyKX0Q3Vi1fpF1PeqD5byLU3C6pLw0yjuEMXV+jW1rNwlE7iiINUu1TGb5ZWwWgLrGKNJZ1KmYkUJ6c5nDMgxqQ3IJxOLSl2hXrYAOAs6KV62kJ6LS5sJc5791XGakXheZMxnZKpcEavBy8zNQrShC6ciWO+KWhu1RBqPBJhUGT2ZZFkfdeqbm7ImnsbSmZiBRnQArx2RYuNIsCdXD0KpA0lErguNMB3l2Icu1hlEyL0AyLJ9reMnfPUhUoYsSdSTiufMOILFxvycc+S5crIe1boytPAH69mHIAAHdueu3c41z9EVQ3cI8CN3DgcNAKlMlKt1E9tv2lLF4S04XmyPZq9TLDuzI8bWe5byjJLkr9JNcvpfA4UbJ/GtuBiADOkD5a9audtn7OvpMLluuphcvtLXVQb5ZvI6BZ2vWm2ilkhgOe3tgdwj77VLABmDSFpEykvLeKQKMNKz6JFkvdAFP0TYi/LRFHRVUTTJiHu1KzHaO2YGHgwsnikEKJjtLQ4L7iuybxciaB6no1vkgXK75tQN47RQuzWZKUOjglAbBBGo/KZ4qWyNd4jPTCb7tc2Am2YavZ0HGbPox4t8BeA2YzkooClHFK7hfLgNnMoAN7FGN3uGXqQKA7ygkqDN2AipmiXO2gG6Jnhl8FAjE0pBcZbxoS8XxCtEffrFZiTgR5MRLXaKgDaHL3vK2wIhHBUbAl1qAQK0plQoJb8nEllbZg0+Hq7rTSrZppLTpO3rENMbYSJHtv+IU6VKmFVNQ37EEliWTt+Es3kIYWoaN7kKF270ol1w4SSyrSdwRCZYNSYZn04tay/FE1joSjK5LJ2KyCQRxT33TsWb53KNXwuJ87LMENNs10gQb2yiGTgYWyLNGeozesXFvmJ5RlTd1BeySQk5poXPhiuIcaPV9b9ZEp6TlDqOYdbagEFGYXvxlBruAxRyDbVNj7VOU5xrBoub7CMqKh9ehRRZ7iKHchCF0kPjvidz7JTFG0ktmbc2HXwvXQ2PNEVPNOiB8WCmpR9bSKntp5sW+MEQ8jFVi4wDjtGfXMF7HWXYJwSIi2ZmeynYKS7DRpNSgEAVNTtRJCc/lUev1ZVAnVoVdWxPWBh3qa5SV4eLsCy0/jIRb0mgKGrMzDKMDuGQpd3oqotmk6iXJomFh3yeJRUN0G49CI656nWeT3OV5PIH9XOP4GErFNaaFVJiifQhIQmGJCPjspCuFJrftnYtsAPGLrIcC5WbeGZxXZAUYpbob4KLBu3gOS3vXF/2UZM2ejF9a6Mk1y1Kcps6oZLy6Yd9WvpHbvxkOXvCOwKyB5RTYOZ7ZbwXRjNq4QDCJ/Jqi9SIRVdlXpGEcoq16EyEuJJW2EMogpUD5dKHixZyFMbTiu4yok2JSlZgjzEV+Ti50pgyJ8jH9C1SVQR3zvotAWb6Hua6PCAG2x558I8UEGHUVWqrp3pThZKOI3mQlASVmalXEZfeZqtDMaIrtdEETJEoXeSIqWwyYlZ+7jNA1ZhEBq9qojcJqWkPDHd5YvtssBQar1gveGqBgrwPtVFdP1PW++G9GZSLkp0CbSMvhZuloCdWshWo0Lc5JxlFTBa1Ax1OHQ8SRW6Gla4X1o8Y0BNeHGwb2LI07Y2tltgtlv7V1lWsJXCJ2Uq6b50iClnzQdw6MOkOY6Mcxd77ezVuo08hEZJEGu1xIlIU0Dk4Q21Lsc6/nQQFdd780GbbFc6PVDBGl2N53M9Q1FNInXOrLy4VyhlthzPe5jjVt6AW4HeO0kTI5mGyE0ksS5+0zKthsA7VhmLxzHxBboMbpXwsieKQbs1+W/CICwwd10sDCniGrKjdN+mIGkaZ74Pu0oV1Oirk2WUBVcHtVDbjXcp8kd5Fhe7E2EwVrhit0OblGvLsxIxLZIWlOXpCpWqDqgvXARASrI0FcHFLgMzLohvS3hmG+58JZTA2dtqNsm4WzoI0dETdzL2cx50UpqUrL7L7YxQlcluKfhM2zfUiobpRDF6qUO4NZfi0nhNtZ7V8BUs/8CgeSsdYLtgWNywKT+lFyqbecoJIgbBQeZqPGoPXHO5PRn6crgSuWHRFhPcjLtfUj5PfzJxtL9qOCjil5L+IZWFQUI4eNrBzOnCuBgy4f00Q7KRSa7mcxXQKvnVXkm3C0M/Q1FOUJQMAy8OmjOioWYqs/i/onpsfm6BiGSb0Yo8+LGxeycc4J/KL/Rlaetosp1E407HRu5AjNZ4QJYo+PRlGVFWS6cnwoZgta4nD/4HoUGT6nBvr3GQoME2SK+XVcx5Og9omM+gL1a58coRhTeW8QKaOlOc+uXWywmSqCnYLesXonMzGsWvWtXCK9nW+85l25KSjrjk4x4XcjEuRKh0IMaguxanagAZHsHhaoYMfJk4AKmAAxhhcTiLlgGrplFSZyjGBBF+RQAeyzivtlB5/L0xH3SCzDHpAcyxlxwgaJakWdiNSl7ByuUC9pKpMYJgJga9KoVmkTKj18mu4mEB/tRfMLExG06wmMUoCXbSaOEnezFgylJToBlWpya1YUCiJ5GbkK+gKnQt+gbWKNj+tXZEebwv0dZNDM7QpSGPuCmKBhS9zQ3kgIlGonqo1+Ul5zNgk6GwjS9+i0y51a/cMYD0pWXENYH3bAFg7F8DaAgDr2gWwSNC7XbxlohSjjRa5UgeCJXhcKcqd92RbT3/vZoOsHTuYkT2AO8Vj9HqNVnlTQMDbdn9s4pQrsXoWshQQ2u3O9LIy9fNEvm1CyTbRCZ8uhdL51HskmYGlC6T46UzXTedyMHTRSwKDhk3ILGDaMJ71c6hjIKn8L6/eIs852ouu5W4NykFb4Zxh9hnjk0QKWAUVDQG7WqWmokWUUrDwkA5OvWScfrpMJGezqKwq6Cd7x6i3HCEa5ubsn25ciZQzzqhfg4VF3LvUupAS4xGEUSnoV5EK07JALQLBAKpkSbZyjg4t9TgrkxFiGLbYFLIwo1Q8C6G+7MeWQDObGm8U+sJXfQYXILkS1rLwGGyZ8yaNwbRWvY/emQvlYNePOV9Auh3V9ptmkzNeKllqmaIxrNAhGsvmtVZZhDh1NA8/PoNLT5sddd1YPtsOdpRdwM6rTf801aIs/ezucnV1btQILoF0xZ1idV4eweNwqMBcDa5Ux2uCPjaNql2t0e6A/2uNhkAX9vy6Um61Op9QRfFQS5W6Aq55Veusga1JSzEeUCodx4gJUOUJs+RPC2Rpje9B+lGmkisN0/aWD/BPcCEhlcvrUWxDxsWX4FAhv4fI/RKIDVJEHRGUPk6bVSrhQETj08y7Dp6UVJKydHrdFEC01yswQJ1c5Au/gUpreZXnQhq148inygoEn5Zua5VnRBlxIudRZruGSHva/YQrBBVUjK7CUPdVpg3SW9UrOkfWdohBQnOv5U3JzR5AGAVloHYZtUI/ttoY2yUe4l5kI3lLy0VPLe6uu9AobbNWFU8GWwSdkcXKrGJz0kG3KsU11CqWi+5JIR+epab+4HSqWxDrY0Lox4ZEiX+3T0VgqoszZelLsazAZLWTAfpSBVoU62V4Oe5tIM6kEWUUpTQ/qJYcqKJZGVRumwWqAIW/UuSeUKOUL1UH4drdTeoJst2dkJFiwfhKH/xCbq3Ph2AzwVQSgXkOHVbZk77HZ+wQNI+Z8vIDVLXdyGsoAb2ysAIpPYZZ9FW8pPaVTQZMKrTOxtiZioqOMiWQsRCIw7jyxSOjimyieCGVFaZdO+wzBS+zPqKAwA9WoqAnAC51lNQyQazCmKSo84hIsqQXmk9ljNniyFFzzSUkm9mSGyCGkakBmYGliowYWkgUAhjNpt91gXyaC2TkBHnaVAJwZYtKWnrYxlGgiUdEtZLg/I1gqVQdqA5RX+2Bdi84ZQSCA71t+iqkl0NhVHojLLPYNEAcjNHMrDyCEVDY2xfv3+cYsS396vjv9Kzpw2wavnz1DCw9DSpVCVq67UjL230zhDrlkept5hRJnx1WfH0cdwrk6h3sBJfOWuwOH4r6BzqzvvGCr7O4i1Gt/TzcKF6dKYGuQwsEB3pLvCfUvOg/ZSRWLqvXD1ogeY2VwNknVzB/W2rzjy2i5xezcsu6ONq57WHACuixU25IDcoV70k6Uj5RjsGsWqzYzEhdqTH6pdjaADhaVFizY43NUs0xOei7u64Ccgq1R7ULiXzUgPxf0n5o7yaqetqSVvIeybJMW9nPcj1TJj8r0yzdDEFn/QW75jg0n70D4pBRqgu/nEUmFMdSEonaIIm5HV+afyZEmRKBk8vuenvupxynSKtiZ9bOwQJ1akXTSiAEbbxXVY8RRChkJaqnUopYAt9pLrAgFYYkjydKLzCWSymY4xbKNeR0YYvTukZXmNaRXfgHW05KRFGysmBSS2ZTXOF7rbyodzYV1ExdUwQ3+ho4Vmv2/FFIUfkEsQUNamuRnm4DVMrwOYqkJ8p+qlTVA96Q4DpI07btGiqeTg7BjpQPWjWhzS5wC9KpP8QcDpptVOFGUXBTvhepXtmZYcoLAUfgOZL4CokhbAGkom2JI6W6WG0d7VCYaVH4UYF8RGW4JJJFgnJ046MUtzSKBzAPnekDEVNjFIGbi90qCnslRNB3Xe45tXBjRoOj99fWjEGaS+v/mIImdhkAglvcMPsNTGFbDppWnRcW9303tpncc0FX4jipyZbWUbBcBD5R1xwrugSkNNFUc/NwyxtKGiiQKvI/2W7TVdbTro6peU3PW+EYq71k5FTSwBSF2K365kqpSC9op7KsIFhaBcFEhbE+aMr30IV+vKT3ZERRy73gJ14l/KdWnRPvsui7LdGF58fKwwRFJ4u1iK3agKpMKCorl+BdAoAGMRrNpGIq1HQoNI/L8DGlKHP4yIhqt/2pAUVIwuP/m2DUlpkYc3NvgSR94yBJVzePx29q0Y+E0L+8RYskm0rVHPWokdowGWoUmCIxqilUifL4/SdVq0qb8FZs6ZrChZTDnj233RwJ6sxSy5cXPlk/ykmkMEBkZVAQxoeMboTKRUWRXT+rkZSjhbPhl6HTPQB719FhCIAn5fJ6Xg9LHAqOIDYRom1ikZtlpRwrWsiXefp4lBwmu7BPJ90E/hEaStRIhqy7SSAjojnUn2OxmZWJGmp4OAuAHWh+NTGuMegKo6eaydhOlhS/nW1osA/YZZ0GB6lnxZhufRj7cVVFlxFJ6aHdSbTSrI1ovliUV6dMzUIqrtn4OPdmxp1qk2/aPT9+XGd3fZMG1H44xRXa1i7zwGrV7KrtWics4YbpZKb7/8yS284wXoVmgf7G2VznG64nBoYUfWDbnyKpSsRN1KQXB6m4+cblvDyE0HzxQZtrYJqyFnusGYBVPbigt5tEgag2lpiiHdjWwz4XoNxgCnits7YZLi5G5F7E1nOpjxn2Js9SbtiYuY29QLunNcKFEcP5mpLezCkU6DuhQ4LdJ3LAwngdcWz9UCf1GKdxnT6YYsW+FPvCMuObKjtJokTUyTxe0YELFbtD47m3szcZGAv7dbltxb0fsA6mr8Z0eGPwvFavVMHudqKdB4yaP7xYdxnqJd1qmVqVfvkbWjimGQhpu5Bz0A9pUMNFPea+Te50PqzFbW8yjqUWu/Ym3YiwmoaUUeXp2sauUXHfBKccdXuZt+OHh0hfzjToQO2jcUyniXHcUSsPNihu4o2wIG0SD9lAx4pJQeQscRpG5bsU6CHsPo9PQRoHTJFFFnvjy3uWUIPV0GJ0SEYxbnLbdgI9kKOAdqDFTlgAAFgpbSsTwEqhBzvdAzoHqfZKxEqumM8X3d3/AUR3MBQ='
MOVE_ACTIONS = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
FIRST_YIELD_DAY = {'WHEAT': 2, 'CARROT': 2, 'TOMATO': 8, 'STRAWBERRY': 10, 'MELON': 10}
ANIMAL_STRUCTURES = {'GOOSE': 'COOP', 'COW': 'PASTURE', 'SHEEP': 'PASTURE'}
PASS = ['PASS']

def _load_actions() -> tuple[dict[str, Any], ...]:
    payload = MODEL_PAYLOAD
    if payload is None:
        model = json.loads(MODEL_PATH.read_text(encoding='utf-8'))
        payload = str(model['actions_zlib_b64'])
    compressed = base64.b64decode(payload)
    actions = json.loads(zlib.decompress(compressed).decode('utf-8'))
    if len(actions) != 720:
        raise ValueError('Distilled calendar must contain 720 records')
    return tuple(actions)
CALENDAR_ACTIONS = _load_actions()

def _tile_at(farm: dict[str, Any], position: tuple[int, int]) -> Any:
    x, y = position
    return farm['tiles'][y][x]

def _shed_adjacent(position: tuple[int, int], board_size: int) -> bool:
    half = board_size // 2
    return position in {(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)}

def _inventory(private: dict[str, Any], worker: int) -> dict[str, Any]:
    inventories = private.get('inventories', [])
    if worker < len(inventories) and isinstance(inventories[worker], dict):
        return inventories[worker]
    return {}

def _valid_action(observation: dict[str, Any], worker: int, position: tuple[int, int], action: list[Any]) -> bool:
    if not action:
        return False
    operation = str(action[0])
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    tile = _tile_at(farm, position)
    inventory = _inventory(private, worker)
    board_size = len(farm['tiles'])
    if operation == 'PASS':
        return True
    if operation in MOVE_ACTIONS:
        x, y = position
        return {'NORTH': y > 0, 'SOUTH': y + 1 < board_size, 'WEST': x > 0, 'EAST': x + 1 < board_size}[operation]
    if operation == 'PLANT':
        return len(action) >= 2 and tile is None and (int(private.get('seeds', {}).get(str(action[1]), 0)) > 0)
    if operation == 'WATER':
        return isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (not tile.get('watered_today', False))
    if operation == 'HARVEST':
        if not isinstance(tile, dict) or int(tile.get('yield_units', 0)) <= 0:
            return False
        if tile.get('kind') != 'PLANT':
            return bool(tile.get('animal'))
        crop = str(tile.get('crop'))
        age = int(observation.get('day', 0)) - int(tile.get('planted_day', 0))
        return age >= FIRST_YIELD_DAY[crop]
    if operation == 'FERTILIZE':
        return isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (int(inventory.get('FERTILIZER', 0)) > 0)
    if operation == 'DIG':
        return tile is not None and (not (isinstance(tile, dict) and tile.get('animal')))
    if operation in {'BUILD_COOP', 'BUILD_PASTURE'}:
        return tile is None
    if operation == 'FEED':
        return isinstance(tile, dict) and tile.get('animal') and (not tile.get('fed_today', False)) and (int(inventory.get('WHEAT', 0)) > 0)
    if operation == 'CARE':
        return isinstance(tile, dict) and tile.get('animal') and (not tile.get('cared_today', False))
    if operation == 'COLLECT_FERTILIZER':
        return isinstance(tile, dict) and tile.get('animal') and bool(tile.get('fertilizer_available', False))
    if operation == 'PICKUP':
        return len(action) >= 2 and _shed_adjacent(position, board_size) and (int(private.get('shed', {}).get(str(action[1]), 0)) > 0)
    if operation == 'DROP':
        return _shed_adjacent(position, board_size) and any((int(quantity) > 0 for quantity in inventory.values()))
    if operation == 'PLACE' and len(action) >= 2:
        item = str(action[1])
        if int(inventory.get(item, 0)) <= 0:
            return False
        if item in ANIMAL_STRUCTURES:
            return isinstance(tile, dict) and tile.get('kind') == ANIMAL_STRUCTURES[item] and (not tile.get('animal'))
        return _shed_adjacent(position, board_size)
    return False

def _local_repair(observation: dict[str, Any], worker: int, position: tuple[int, int]) -> list[Any]:
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    tile = _tile_at(farm, position)
    inventory = _inventory(private, worker)
    board_size = len(farm['tiles'])
    if isinstance(tile, dict) and int(tile.get('yield_units', 0)) > 0:
        action = ['HARVEST']
        if _valid_action(observation, worker, position, action):
            return action
    if isinstance(tile, dict) and tile.get('animal'):
        if not tile.get('fed_today', False) and int(inventory.get('WHEAT', 0)) > 0:
            return ['FEED']
        if tile.get('fed_today', False) and (not tile.get('cared_today', False)):
            return ['CARE']
        if tile.get('fertilizer_available', False):
            return ['COLLECT_FERTILIZER']
    if isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (not tile.get('watered_today', False)) and (int(tile.get('consecutive_unwatered', 0)) >= 1):
        return ['WATER']
    if _shed_adjacent(position, board_size) and any((int(quantity) > 0 for quantity in inventory.values())):
        return ['DROP']
    return PASS

def _sanitize_units(observation: dict[str, Any], planned: dict[str, Any]) -> tuple[list[Any], list[list[Any]]]:
    player = int(observation['player'])
    farm = observation['farms'][player]
    positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
    planned_actions = [planned.get('farmer', PASS)]
    planned_actions.extend(planned.get('hands', []))
    sanitized = []
    for worker, position in enumerate(positions):
        action = planned_actions[worker] if worker < len(planned_actions) and isinstance(planned_actions[worker], list) else PASS
        sanitized.append(list(action) if _valid_action(observation, worker, position, action) else _local_repair(observation, worker, position))
    available_seeds = Counter(observation['private'].get('seeds', {}))
    for crop in tuple(available_seeds):
        planters = [worker for worker, action in enumerate(sanitized) if action[:2] == ['PLANT', crop]]
        for worker in planters[available_seeds[crop]:]:
            sanitized[worker] = PASS
    return (sanitized[0], sanitized[1:])

def calendar_decide(observation: dict[str, Any]) -> dict[str, Any]:
    next_record = int(observation.get('step', 0)) + 1
    if next_record >= len(CALENDAR_ACTIONS):
        return {'farmer': PASS, 'hands': [], 'market': []}
    planned = CALENDAR_ACTIONS[next_record]
    return {'farmer': list(planned.get('farmer', PASS)), 'hands': [list(action) for action in planned.get('hands', [])], 'market': [list(order) for order in planned.get('market', [])]}
'Deterministic shortest-path primitives for the obstacle-free farm grid.'
from collections.abc import Iterable
Position = tuple[int, int]
Action = list[str]

def distance(origin: Position, target: Position) -> int:
    """Return the exact shortest path length on the farm grid."""
    return abs(origin[0] - target[0]) + abs(origin[1] - target[1])

def step_toward(origin: Position, target: Position, action_at_target: Action) -> Action:
    """Take one deterministic shortest-path step or act at the target."""
    if origin == target:
        return action_at_target
    if target[0] < origin[0]:
        return ['WEST']
    if target[0] > origin[0]:
        return ['EAST']
    if target[1] < origin[1]:
        return ['NORTH']
    return ['SOUTH']

def nearest_position(origin: Position, targets: Iterable[Position]) -> Position:
    """Return the nearest target with stable row-major tie-breaking."""
    return min(targets, key=lambda target: (distance(origin, target), target[1], target[0]))

def pair_route_cost(positions: tuple[Position, Position], target: Position) -> tuple[int, int]:
    """Rank a paired route by completion time, then total travel."""
    distances = tuple((distance(position, target) for position in positions))
    return (max(distances), sum(distances))
'Public observation features and inference for learned macro policies.'
from collections import Counter
from math import sqrt
from typing import Any
ARM_COMPACT = 0
ARM_EXPANDED = 1
ARM_COMPACT_CROP = 2
ARM_EXPANDED_CROP = 3
MACRO_ARMS = (ARM_COMPACT, ARM_EXPANDED, ARM_COMPACT_CROP, ARM_EXPANDED_CROP)
FEATURE_NAMES = ('player', 'own_money_k', 'opponent_money_k', 'money_lead_k', 'opponent_hands', 'opponent_land', 'opponent_wheat', 'opponent_nonwheat', 'opponent_cows', 'opponent_sheep', 'opponent_geese', 'opponent_structures', 'opponent_weeds', 'price_wheat', 'price_strawberry', 'price_melon', 'price_milk', 'price_wool', 'price_fertilizer', 'shops_wheat', 'shops_strawberry', 'shops_milk', 'shops_wool')
WHEAT_SHOPS = {'BAKERY', 'BRUNCH_SPOT', 'FARMERS_MARKET', 'ICE_CREAM_SHOP', 'PIZZA_SHOP'}
STRAWBERRY_SHOPS = {'BRUNCH_SPOT', 'FARMERS_MARKET', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP'}
MILK_SHOPS = {'ICE_CREAM_SHOP', 'PIZZA_SHOP', 'SMOOTHIE_SHOP'}

def _public_counts(farm: dict[str, Any]) -> dict[str, Counter[str]]:
    counts = {'crops': Counter(), 'animals': Counter(), 'structures': Counter(), 'terrain': Counter()}
    for row in farm.get('tiles', []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get('kind') == 'PLANT':
                counts['crops'][str(tile.get('crop', 'UNKNOWN'))] += 1
            if tile.get('animal'):
                counts['animals'][str(tile['animal'])] += 1
            if tile.get('kind') in {'COOP', 'PASTURE'}:
                counts['structures'][str(tile['kind'])] += 1
            if tile.get('kind') == 'WEED':
                counts['terrain']['WEED'] += 1
    return counts

def extract_macro_features(observation: dict[str, Any]) -> dict[str, float]:
    """Extract only state that is public to both players."""
    player = int(observation['player'])
    farms = observation['farms']
    own = farms[player]
    opponent = farms[1 - player]
    counts = _public_counts(opponent)
    crops = counts['crops']
    animals = counts['animals']
    prices = observation.get('market', {}).get('prices', {})
    shops = Counter(observation.get('town', {}).get('unlocked_shops', []))
    own_money = float(own.get('money', 0))
    opponent_money = float(opponent.get('money', 0))
    features = {'player': float(player), 'own_money_k': own_money / 1000.0, 'opponent_money_k': opponent_money / 1000.0, 'money_lead_k': (own_money - opponent_money) / 1000.0, 'opponent_hands': float(len(opponent.get('hands', []))), 'opponent_land': float(len(opponent.get('unlocked_quadrants', []))), 'opponent_wheat': float(crops['WHEAT']), 'opponent_nonwheat': float(sum(crops.values()) - crops['WHEAT']), 'opponent_cows': float(animals['COW']), 'opponent_sheep': float(animals['SHEEP']), 'opponent_geese': float(animals['GOOSE']), 'opponent_structures': float(sum(counts['structures'].values())), 'opponent_weeds': float(counts['terrain']['WEED']), 'price_wheat': float(prices.get('WHEAT', 0)) / 25.0, 'price_strawberry': float(prices.get('STRAWBERRY', 0)) / 120.0, 'price_melon': float(prices.get('MELON', 0)) / 250.0, 'price_milk': float(prices.get('MILK', 0)) / 160.0, 'price_wool': float(prices.get('WOOL', 0)) / 200.0, 'price_fertilizer': float(prices.get('FERTILIZER', 0)) / 100.0, 'shops_wheat': float(sum((shops[shop] for shop in WHEAT_SHOPS))), 'shops_strawberry': float(sum((shops[shop] for shop in STRAWBERRY_SHOPS))), 'shops_milk': float(sum((shops[shop] for shop in MILK_SHOPS))), 'shops_wool': float(shops['YARN_STORE'])}
    return {name: features[name] for name in FEATURE_NAMES}

def select_macro_arm(model: dict[str, Any], features: dict[str, float]) -> int:
    """Evaluate a learned macro policy."""
    if model.get('type') == 'knn':
        return _select_knn_arm(model, features)
    node = model
    while 'arm' not in node:
        feature = str(node['feature'])
        branch = 'left' if features[feature] <= float(node['threshold']) else 'right'
        node = node[branch]
    arm = int(node['arm'])
    if arm not in MACRO_ARMS:
        raise ValueError(f'Unknown macro arm: {arm}')
    return arm

def _select_knn_arm(model: dict[str, Any], features: dict[str, float]) -> int:
    names = [str(name) for name in model['features']]
    means = model['means']
    scales = model['scales']
    distances = []
    for example in model['examples']:
        squared = sum((((features[name] - float(example['features'][name])) / float(scales[name])) ** 2 for name in names))
        distances.append((sqrt(squared), example))
    neighbors = sorted(distances, key=lambda item: item[0])[:int(model['k'])]
    power = float(model.get('distance_power', 1.0))
    scores = {}
    for arm in MACRO_ARMS:
        weighted = 0.0
        weight_sum = 0.0
        for distance, example in neighbors:
            if str(arm) not in example['outcomes']:
                continue
            weight = 1.0 if power == 0 else 1.0 / (distance + 0.1) ** power
            weighted += weight * float(example['outcomes'][str(arm)]['utility'])
            weight_sum += weight
        if weight_sum > 0:
            scores[arm] = weighted / weight_sum
    if not scores:
        raise ValueError('KNN macro model has no compatible arm outcomes')
    return max(scores, key=lambda arm: (scores[arm], arm))
'Decision-time workload features for live macro selection.'
from typing import Any
PREMIUM_SERVICE_AGES = {'MELON': frozenset({6, 7, 8, 9, 10}), 'STRAWBERRY': frozenset({9, 11, 13, 15})}
LIVE_FEATURE_NAMES = FEATURE_NAMES + ('own_hands', 'own_land', 'own_wheat', 'own_nonwheat', 'own_strawberries', 'own_unwatered_crops', 'own_stressed_crops', 'own_harvestable_crop_units', 'own_animals', 'own_cows', 'own_sheep', 'own_geese', 'own_due_feed', 'own_due_care', 'own_collectable_animal_units', 'own_fertilizer_stock', 'own_service_tasks_per_worker', 'own_fertilizer_carriers', 'own_carried_fertilizer', 'own_due_melons', 'own_due_strawberries', 'own_unfertilized_due_melons', 'own_unfertilized_due_strawberries', 'own_unfertilized_due_premium', 'own_workers_on_due_melons', 'own_workers_on_due_strawberries', 'own_workers_on_due_premium', 'own_min_carrier_distance_to_due_melons', 'own_min_carrier_distance_to_due_strawberries', 'own_min_carrier_distance_to_due_premium', 'own_mean_worker_distance_to_due_premium', 'own_pending_feed', 'own_pending_care', 'own_pending_animal_harvests', 'own_pending_fertilizer_collection', 'own_pending_animal_service_per_worker')

def extract_live_macro_features(observation: dict[str, Any]) -> dict[str, float]:
    """Add own service burden to the public opponent and market context."""
    features = extract_macro_features(observation)
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation.get('private', {})
    crops = []
    animals = []
    for row in farm.get('tiles', []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get('kind') == 'PLANT':
                crops.append(tile)
            if tile.get('animal'):
                animals.append(tile)
    unwatered = sum((not tile.get('watered_today', False) for tile in crops))
    harvestable_crops = sum((int(tile.get('yield_units', 0)) for tile in crops))
    due_feed = sum((not tile.get('fed_today', False) and int(tile.get('consecutive_unfed', 0)) >= 1 for tile in animals))
    due_care = sum((tile.get('fed_today', False) and (not tile.get('cared_today', False)) for tile in animals))
    collectable_animals = sum((int(tile.get('yield_units', 0)) for tile in animals))
    service_tasks = unwatered + sum((int(tile.get('yield_units', 0)) > 0 for tile in crops)) + due_feed + due_care + sum((int(tile.get('yield_units', 0)) > 0 for tile in animals))
    workers = 1 + len(farm.get('hands', []))
    inventories = private.get('inventories', [])
    positions = [tuple(farm.get('farmer', (0, 0))), *(tuple(position) for position in farm.get('hands', []))]
    carried_fertilizer = [int(inventory.get('FERTILIZER', 0)) if isinstance(inventory, dict) else 0 for inventory in inventories[:len(positions)]]
    carriers = [worker for worker, quantity in enumerate(carried_fertilizer) if quantity > 0]
    day = int(observation.get('day', 0))
    due_by_crop: dict[str, list[tuple[int, int]]] = {'MELON': [], 'STRAWBERRY': []}
    unfertilized_by_crop = {'MELON': 0, 'STRAWBERRY': 0}
    for y, row in enumerate(farm.get('tiles', [])):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            crop = str(tile.get('crop', ''))
            if crop not in PREMIUM_SERVICE_AGES:
                continue
            age = day - int(tile.get('planted_day', day))
            if age not in PREMIUM_SERVICE_AGES[crop] or tile.get('watered_today', False):
                continue
            due_by_crop[crop].append((x, y))
            unfertilized_by_crop[crop] += int(tile.get('fertilized_until_day', -1)) < day
    due_premium = [target for crop in PREMIUM_SERVICE_AGES for target in due_by_crop[crop]]
    board_diameter = max(1, 2 * (len(farm.get('tiles', [])) - 1))
    no_target_distance = float(board_diameter + 1)
    carrier_distances = [distance(positions[worker], target) for worker in carriers for target in due_premium]
    minimum_carrier_distance_by_crop = {crop: float(min((distance(positions[worker], target) for worker in carriers for target in targets), default=no_target_distance)) for crop, targets in due_by_crop.items()}
    worker_target_distances = [min((distance(position, target) for position in positions)) for target in due_premium] if positions else []
    pending_feed = sum((not tile.get('fed_today', False) for tile in animals))
    pending_care = sum((not tile.get('cared_today', False) for tile in animals))
    pending_animal_harvests = sum((int(tile.get('yield_units', 0)) > 0 for tile in animals))
    pending_fertilizer_collection = sum((tile.get('fertilizer_available', False) for tile in animals))
    pending_animal_service = pending_feed + pending_care + pending_animal_harvests + pending_fertilizer_collection
    fertilizer_stock = int(private.get('shed', {}).get('FERTILIZER', 0)) + sum((int(inventory.get('FERTILIZER', 0)) for inventory in inventories if isinstance(inventory, dict)))
    own_features = {'own_hands': float(len(farm.get('hands', []))), 'own_land': float(len(farm.get('unlocked_quadrants', []))), 'own_wheat': float(sum((tile.get('crop') == 'WHEAT' for tile in crops))), 'own_nonwheat': float(sum((tile.get('crop') != 'WHEAT' for tile in crops))), 'own_strawberries': float(sum((tile.get('crop') == 'STRAWBERRY' for tile in crops))), 'own_unwatered_crops': float(unwatered), 'own_stressed_crops': float(sum((int(tile.get('consecutive_unwatered', 0)) > 0 for tile in crops))), 'own_harvestable_crop_units': float(harvestable_crops), 'own_animals': float(len(animals)), 'own_cows': float(sum((tile.get('animal') == 'COW' for tile in animals))), 'own_sheep': float(sum((tile.get('animal') == 'SHEEP' for tile in animals))), 'own_geese': float(sum((tile.get('animal') == 'GOOSE' for tile in animals))), 'own_due_feed': float(due_feed), 'own_due_care': float(due_care), 'own_collectable_animal_units': float(collectable_animals), 'own_fertilizer_stock': float(fertilizer_stock), 'own_service_tasks_per_worker': service_tasks / workers, 'own_fertilizer_carriers': float(len(carriers)), 'own_carried_fertilizer': float(sum(carried_fertilizer)), 'own_due_melons': float(len(due_by_crop['MELON'])), 'own_due_strawberries': float(len(due_by_crop['STRAWBERRY'])), 'own_unfertilized_due_melons': float(unfertilized_by_crop['MELON']), 'own_unfertilized_due_strawberries': float(unfertilized_by_crop['STRAWBERRY']), 'own_unfertilized_due_premium': float(sum(unfertilized_by_crop.values())), 'own_workers_on_due_melons': float(sum((position in due_by_crop['MELON'] for position in positions))), 'own_workers_on_due_strawberries': float(sum((position in due_by_crop['STRAWBERRY'] for position in positions))), 'own_workers_on_due_premium': float(sum((position in due_premium for position in positions))), 'own_min_carrier_distance_to_due_melons': minimum_carrier_distance_by_crop['MELON'], 'own_min_carrier_distance_to_due_strawberries': minimum_carrier_distance_by_crop['STRAWBERRY'], 'own_min_carrier_distance_to_due_premium': float(min(carrier_distances, default=no_target_distance)), 'own_mean_worker_distance_to_due_premium': sum(worker_target_distances) / len(worker_target_distances) if worker_target_distances else no_target_distance, 'own_pending_feed': float(pending_feed), 'own_pending_care': float(pending_care), 'own_pending_animal_harvests': float(pending_animal_harvests), 'own_pending_fertilizer_collection': float(pending_fertilizer_collection), 'own_pending_animal_service_per_worker': pending_animal_service / workers}
    combined = features | own_features
    return {name: combined[name] for name in LIVE_FEATURE_NAMES}
'Typed macro decisions for a residual Kaggriculture policy.'
from dataclasses import dataclass
from enum import IntEnum

class LaborDecision(IntEnum):
    KEEP = 0
    REDUCE_ONE = 1
    ADD_ONE = 2

class LandDecision(IntEnum):
    KEEP = 0
    BUY_NEXT = 1

class CropDecision(IntEnum):
    KEEP = 0
    DEMAND_BEST = 1
    WHEAT = 2
    STRAWBERRY = 3
    MELON = 4

class ServiceDecision(IntEnum):
    KEEP = 0
    SPARSE = 1
    FULL = 2
    ABANDON_LOW_VALUE = 3

class MarketDecision(IntEnum):
    KEEP = 0
    PRESERVE_CASH = 1
    PACE_SALES = 2
    LIQUIDATE = 3

class RecoveryDecision(IntEnum):
    KEEP = 0
    REPAIR_STATE_DRIFT = 1
ACTION_HEAD_SIZES = (len(LaborDecision), len(LandDecision), len(CropDecision), len(ServiceDecision), len(MarketDecision), len(RecoveryDecision))

@dataclass(frozen=True)
class ResidualAction:
    """One factored correction to the trusted calendar policy."""
    labor: LaborDecision = LaborDecision.KEEP
    land: LandDecision = LandDecision.KEEP
    crop: CropDecision = CropDecision.KEEP
    service: ServiceDecision = ServiceDecision.KEEP
    market: MarketDecision = MarketDecision.KEEP
    recovery: RecoveryDecision = RecoveryDecision.KEEP

    @property
    def is_keep_calendar(self) -> bool:
        return self == KEEP_CALENDAR

    def head_indices(self) -> tuple[int, ...]:
        """Return one categorical index for each policy head."""
        return tuple((int(value) for value in (self.labor, self.land, self.crop, self.service, self.market, self.recovery)))
KEEP_CALENDAR = ResidualAction()
'Stable state-vector contract for learned residual policies.'
from dataclasses import dataclass
from math import isfinite
from typing import Any
CLOCK_FEATURE_NAMES = ('day_fraction', 'hour_fraction', 'episode_fraction')
BASELINE_FEATURE_NAMES = ('baseline_hands', 'baseline_moves', 'baseline_plants', 'baseline_waters', 'baseline_harvests', 'baseline_animal_services', 'baseline_passes', 'baseline_market_orders', 'baseline_hires', 'baseline_land_orders', 'baseline_seed_units', 'baseline_animal_units', 'baseline_sell_units')
STATE_FEATURE_NAMES = (*CLOCK_FEATURE_NAMES, *LIVE_FEATURE_NAMES, *BASELINE_FEATURE_NAMES)
MOVE_ACTIONS = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
ANIMAL_SERVICE_ACTIONS = {'FEED', 'CARE', 'COLLECT_FERTILIZER'}

@dataclass(frozen=True)
class EncodedState:
    """Named vector passed to a learned policy."""
    names: tuple[str, ...]
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.names) != len(self.values):
            raise ValueError('Feature names and values must have equal length')
        if not all((isfinite(value) for value in self.values)):
            raise ValueError('RL state contains a non-finite feature')

    def as_dict(self) -> dict[str, float]:
        return dict(zip(self.names, self.values, strict=True))

def _operation(action: Any) -> str:
    if not isinstance(action, list) or not action:
        return 'PASS'
    return str(action[0])

def _order_units(order: Any) -> int:
    if not isinstance(order, list):
        return 0
    if len(order) >= 3:
        return max(0, int(order[2]))
    return 1

def summarize_baseline_action(action: dict[str, Any]) -> dict[str, float]:
    """Describe what the trusted policy intends to do this transition."""
    farmer = action.get('farmer', ['PASS'])
    hands = action.get('hands', [])
    unit_operations = [_operation(farmer), *(_operation(hand_action) for hand_action in hands)]
    market = [order for order in action.get('market', []) if isinstance(order, list) and order]

    def market_units(operation: str) -> int:
        return sum((_order_units(order) for order in market if str(order[0]) == operation))
    return {'baseline_hands': float(len(hands)), 'baseline_moves': float(sum((operation in MOVE_ACTIONS for operation in unit_operations))), 'baseline_plants': float(unit_operations.count('PLANT')), 'baseline_waters': float(unit_operations.count('WATER')), 'baseline_harvests': float(unit_operations.count('HARVEST')), 'baseline_animal_services': float(sum((operation in ANIMAL_SERVICE_ACTIONS for operation in unit_operations))), 'baseline_passes': float(unit_operations.count('PASS')), 'baseline_market_orders': float(len(market)), 'baseline_hires': float(sum((str(order[0]) == 'HIRE' for order in market))), 'baseline_land_orders': float(sum((str(order[0]) == 'BUY_LAND' for order in market))), 'baseline_seed_units': float(market_units('BUY_SEED')), 'baseline_animal_units': float(market_units('BUY_ANIMAL')), 'baseline_sell_units': float(market_units('SELL'))}

def encode_state(observation: dict[str, Any], baseline_action: dict[str, Any]) -> EncodedState:
    """Encode legal observation data and the calendar's intended action."""
    day = int(observation.get('day', 0))
    hour = int(observation.get('hour', 0))
    step = int(observation.get('step', day * 24 + hour))
    values = {'day_fraction': min(max(day / 29.0, 0.0), 1.0), 'hour_fraction': min(max(hour / 23.0, 0.0), 1.0), 'episode_fraction': min(max(step / 718.0, 0.0), 1.0), **extract_live_macro_features(observation), **summarize_baseline_action(baseline_action)}
    return EncodedState(names=STATE_FEATURE_NAMES, values=tuple((float(values[name]) for name in STATE_FEATURE_NAMES)))
'Policy interface used by training and deployment adapters.'
from typing import Protocol

class ResidualPolicy(Protocol):

    def select_action(self, state: EncodedState) -> ResidualAction:
        """Choose a correction to the trusted calendar."""

class KeepCalendarPolicy:
    """Reference policy and mandatory training baseline."""

    def select_action(self, state: EncodedState) -> ResidualAction:
        del state
        return KEEP_CALENDAR
calendar = calendar_decide
'Fail-closed bridge from a residual policy to a Kaggle agent.'
from typing import Any, Callable, Protocol
AgentAction = dict[str, Any]
Baseline = Callable[[dict[str, Any]], AgentAction]

class UnsupportedResidualAction(RuntimeError):
    """Raised before an unimplemented learned action can reach Kaggle."""

class ResidualExecutor(Protocol):

    def apply(self, observation: dict[str, Any], baseline_action: AgentAction, residual_action: ResidualAction) -> AgentAction:
        """Safely translate one macro correction into primitive actions."""

def clone_action(action: AgentAction) -> AgentAction:
    return {'farmer': list(action.get('farmer', ['PASS'])), 'hands': [list(item) for item in action.get('hands', [])], 'market': [list(item) for item in action.get('market', [])]}

class KeepOnlyExecutor:
    """Phase-zero executor that permits no behavioral drift."""

    def apply(self, observation: dict[str, Any], baseline_action: AgentAction, residual_action: ResidualAction) -> AgentAction:
        del observation
        if not residual_action.is_keep_calendar:
            raise UnsupportedResidualAction(f'Residual execution is not implemented for {residual_action!r}')
        return clone_action(baseline_action)

def build_residual_agent(policy: ResidualPolicy, *, baseline: Baseline=calendar, executor: ResidualExecutor | None=None) -> Baseline:
    """Create a Kaggle callable while preserving deterministic safety."""
    selected_executor = executor or KeepOnlyExecutor()

    def agent(observation: dict[str, Any]) -> AgentAction:
        baseline_action = baseline(observation)
        state = encode_state(observation, baseline_action)
        residual_action = policy.select_action(state)
        return selected_executor.apply(observation, baseline_action, residual_action)
    return agent
'Candidate A: guarded calendar recovery and live terminal liquidation.'
import copy
from dataclasses import dataclass, field
from typing import Any
PASS = ['PASS']
MOVE_ACTIONS = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
FINAL_EXECUTABLE_STEP = 718
TERMINAL_PLANNING_STEP = 700
TERMINAL_RETURN_STEP = 716
TERMINAL_SELL_STEP = 717
SHED_CAPACITY = 100
SELLABLE_PRODUCTS = ('MELON', 'MILK', 'WOOL', 'STRAWBERRY', 'TOMATO', 'CARROT', 'EGG', 'WHEAT', 'FERTILIZER')
ANIMAL_STRUCTURES = {'GOOSE': 'COOP', 'COW': 'PASTURE', 'SHEEP': 'PASTURE'}
RECOVERABLE_SETUP = {'PLANT', 'BUILD_COOP', 'BUILD_PASTURE'}
LOCKED_TILE_OPERATIONS = {'PLANT', 'WATER', 'HARVEST', 'FERTILIZE', 'DIG', 'BUILD_COOP', 'BUILD_PASTURE', 'FEED', 'CARE', 'COLLECT_FERTILIZER'}

@dataclass(frozen=True)
class PendingRepair:
    position: tuple[int, int]
    action: tuple[Any, ...]
    expires_step: int

@dataclass
class TerminalCommitment:
    target: tuple[int, int]
    shed: tuple[int, int]
    needs_water: bool
    phase: str = 'target'

@dataclass
class EpisodeRecovery:
    last_step: int = -1
    pending: dict[int, PendingRepair] = field(default_factory=dict)
    terminal: dict[int, TerminalCommitment] = field(default_factory=dict)

@dataclass(frozen=True)
class GuardEvent:
    guard_type: str
    worker: int
    step: int
    original_action: tuple[Any, ...]
    replacement_action: tuple[Any, ...]
    detail: str = ''

@dataclass
class CandidateATelemetry:
    """Structured residual counters for benchmark output only."""
    events: list[GuardEvent] = field(default_factory=list)
    prevented_invalid: int = 0
    recovered_units: int = 0
    sold_units: int = 0
    terminal_inventory_before: dict[str, int] = field(default_factory=dict)
    terminal_inventory_after: dict[str, int] = field(default_factory=dict)

    def record(self, *, guard_type: str, worker: int, step: int, original: list[Any], replacement: list[Any], detail: str='') -> None:
        if original == replacement:
            return
        self.events.append(GuardEvent(guard_type=guard_type, worker=worker, step=step, original_action=tuple(original), replacement_action=tuple(replacement), detail=detail))

    def summarize(self) -> dict[str, Any]:
        by_guard: dict[str, int] = {}
        for event in self.events:
            by_guard[event.guard_type] = by_guard.get(event.guard_type, 0) + 1
        return {'guard_firings': len(self.events), 'guard_types': by_guard, 'prevented_invalid': self.prevented_invalid, 'recovered_units': self.recovered_units, 'sold_units': self.sold_units, 'terminal_inventory_before': dict(self.terminal_inventory_before), 'terminal_inventory_after': dict(self.terminal_inventory_after), 'events': [{'guard_type': event.guard_type, 'worker': event.worker, 'step': event.step, 'original_action': list(event.original_action), 'replacement_action': list(event.replacement_action), 'detail': event.detail} for event in self.events]}

class CandidateAPolicy:
    """Enable only the deterministic Candidate A residual Options."""

    def __init__(self, *, enable_recovery: bool=True, enable_liquidation: bool=True, enable_terminal_commitments: bool=True) -> None:
        self._enable_recovery = enable_recovery
        self._enable_liquidation = enable_liquidation
        self._terminal_start = TERMINAL_PLANNING_STEP if enable_terminal_commitments else TERMINAL_RETURN_STEP

    def select_action(self, state: EncodedState) -> ResidualAction:
        features = state.as_dict()
        step = round(features['episode_fraction'] * FINAL_EXECUTABLE_STEP)
        market = MarketDecision.LIQUIDATE if self._enable_liquidation and step >= self._terminal_start else MarketDecision.KEEP
        return ResidualAction(market=market, recovery=RecoveryDecision.REPAIR_STATE_DRIFT if self._enable_recovery else RecoveryDecision.KEEP)

class CandidateAExecutor(ResidualExecutor):
    """Apply narrow recovery and liquidation without replacing strategy."""

    def __init__(self, baseline: Baseline, *, telemetry: CandidateATelemetry | None=None) -> None:
        self._baseline = baseline
        self._telemetry = telemetry
        self._episodes: dict[int, EpisodeRecovery] = {}

    def apply(self, observation: dict[str, Any], baseline_action: AgentAction, residual_action: ResidualAction) -> AgentAction:
        self._require_supported(residual_action)
        action = clone_action(baseline_action)
        player = int(observation['player'])
        step = int(observation.get('step', 0))
        episode = self._episode(player, step)
        if residual_action.recovery == RecoveryDecision.REPAIR_STATE_DRIFT:
            action = self._repair_units(observation, action, episode)
        if residual_action.market == MarketDecision.LIQUIDATE:
            action = self._terminal_units(observation, action, episode)
            if step >= TERMINAL_SELL_STEP:
                before = _shed_inventory(observation)
                market = self._terminal_market(observation, action)
                after = _projected_shed_after_market(before, market)
                if self._telemetry is not None:
                    self._telemetry.terminal_inventory_before = before
                    self._telemetry.terminal_inventory_after = after
                    self._telemetry.sold_units += sum((int(order[2]) for order in market if len(order) >= 3 and str(order[0]) == 'SELL'))
                action['market'] = market
        episode.last_step = step
        return action

    def _require_supported(self, action: ResidualAction) -> None:
        unsupported = action.labor != LaborDecision.KEEP or action.land != LandDecision.KEEP or action.crop != CropDecision.KEEP or (action.service != ServiceDecision.KEEP) or (action.market not in {MarketDecision.KEEP, MarketDecision.LIQUIDATE}) or (action.recovery not in {RecoveryDecision.KEEP, RecoveryDecision.REPAIR_STATE_DRIFT})
        if unsupported:
            raise UnsupportedResidualAction(f'Candidate A cannot execute {action!r}')

    def _episode(self, player: int, step: int) -> EpisodeRecovery:
        episode = self._episodes.setdefault(player, EpisodeRecovery())
        if step == 0 or step <= episode.last_step:
            episode = EpisodeRecovery()
            self._episodes[player] = episode
        return episode

    def _repair_units(self, observation: dict[str, Any], action: AgentAction, episode: EpisodeRecovery) -> AgentAction:
        player = int(observation['player'])
        step = int(observation.get('step', 0))
        farm = observation['farms'][player]
        positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
        baseline_planned = [action.get('farmer', PASS), *action.get('hands', [])]
        planned = [list(baseline_planned[worker]) if worker < len(baseline_planned) else list(PASS) for worker in range(len(positions))]
        for worker in range(len(positions), len(baseline_planned)):
            if self._telemetry is not None:
                stale = list(baseline_planned[worker])
                self._telemetry.record(guard_type='hand_align', worker=worker, step=step, original=stale, replacement=list(PASS), detail='dropped_stale_calendar_hand')
                self._telemetry.prevented_invalid += 1
        for worker, position in enumerate(positions):
            pending = episode.pending.get(worker)
            if pending is not None:
                replacement = self._continue_repair(observation, worker, position, pending)
                if replacement is not None:
                    original = list(planned[worker])
                    planned[worker] = replacement
                    if self._telemetry is not None:
                        self._telemetry.record(guard_type='pending_repair', worker=worker, step=step, original=original, replacement=replacement, detail='continue')
                    if replacement[0] == 'PLANT':
                        episode.pending[worker] = PendingRepair(position=position, action=('WATER',), expires_step=step + 1)
                    else:
                        episode.pending.pop(worker, None)
                    continue
                if self._telemetry is not None:
                    self._telemetry.record(guard_type='pending_repair', worker=worker, step=step, original=list(planned[worker]), replacement=list(planned[worker]), detail='cancelled')
                episode.pending.pop(worker, None)
            tile = _tile_at(farm, position)
            operation = str(planned[worker][0]) if planned[worker] else 'PASS'
            if operation in RECOVERABLE_SETUP and _is_weed(tile) and _repair_has_time(observation, operation) and self._repair_preserves_schedule(observation, worker, operation):
                original = list(planned[worker])
                episode.pending[worker] = PendingRepair(position=position, action=tuple(original), expires_step=step + (2 if operation == 'PLANT' else 1))
                planned[worker] = ['DIG']
                if self._telemetry is not None:
                    self._telemetry.record(guard_type='weed_dig', worker=worker, step=step, original=original, replacement=['DIG'])
                    self._telemetry.recovered_units += 1
            elif operation in LOCKED_TILE_OPERATIONS and _is_locked(tile):
                original = list(planned[worker])
                planned[worker] = list(PASS)
                if self._telemetry is not None:
                    self._telemetry.record(guard_type='locked_quadrant', worker=worker, step=step, original=original, replacement=list(PASS), detail='calendar_targeted_unpurchased_land')
                    self._telemetry.prevented_invalid += 1
            elif operation in LOCKED_TILE_OPERATIONS and operation != 'DIG' and _is_weed(tile):
                original = list(planned[worker])
                planned[worker] = ['DIG']
                if self._telemetry is not None:
                    self._telemetry.record(guard_type='weed_clear', worker=worker, step=step, original=original, replacement=['DIG'], detail='doomed_action_on_weed_cleared_in_place')
                    self._telemetry.prevented_invalid += 1
        return {'farmer': planned[0], 'hands': planned[1:], 'market': [list(order) for order in action.get('market', [])]}

    def _repair_preserves_schedule(self, observation: dict[str, Any], worker: int, operation: str) -> bool:
        next_action = self._future_action(observation, worker, 1)
        if operation == 'PLANT':
            return next_action == ['WATER'] and self._future_action(observation, worker, 2) == PASS
        return next_action == PASS

    def _future_action(self, observation: dict[str, Any], worker: int, offset: int) -> list[Any] | None:
        future = copy.deepcopy(observation)
        step = int(observation.get('step', 0)) + offset
        future['step'] = step
        future['day'] = step // 24
        future['hour'] = step % 24
        action = self._baseline(future)
        actions = [action.get('farmer', PASS), *action.get('hands', [])]
        if worker >= len(actions):
            return None
        worker_action = actions[worker]
        return list(worker_action) if isinstance(worker_action, list) else None

    def _continue_repair(self, observation: dict[str, Any], worker: int, position: tuple[int, int], pending: PendingRepair) -> list[Any] | None:
        step = int(observation.get('step', 0))
        if step > pending.expires_step or position != pending.position:
            return None
        player = int(observation['player'])
        farm = observation['farms'][player]
        private = observation['private']
        tile = _tile_at(farm, position)
        operation = str(pending.action[0])
        if operation == 'PLANT':
            crop = str(pending.action[1])
            if tile is None and int(private['seeds'].get(crop, 0)) > 0:
                return list(pending.action)
            return None
        if operation in {'BUILD_COOP', 'BUILD_PASTURE'}:
            return list(pending.action) if tile is None else None
        if operation == 'WATER':
            if isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (not tile.get('watered_today', False)):
                return ['WATER']
        return None

    def _terminal_units(self, observation: dict[str, Any], action: AgentAction, episode: EpisodeRecovery) -> AgentAction:
        player = int(observation['player'])
        step = int(observation.get('step', 0))
        farm = observation['farms'][player]
        private = observation['private']
        positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
        planned = [action['farmer'], *action['hands']]
        shed_tiles = _shed_access_tiles(len(farm['tiles']))
        transitions = FINAL_EXECUTABLE_STEP - step + 1
        reserved = {commitment.target for commitment in episode.terminal.values()}
        for worker, position in enumerate(positions):
            commitment = episode.terminal.get(worker)
            if commitment is None and step < TERMINAL_RETURN_STEP:
                commitment = self._find_terminal_commitment(observation, worker, position, reserved)
                if commitment is not None:
                    episode.terminal[worker] = commitment
                    reserved.add(commitment.target)
                    if self._telemetry is not None:
                        self._telemetry.record(guard_type='terminal_commitment', worker=worker, step=step, original=list(planned[worker]), replacement=list(planned[worker]), detail='started')
            if commitment is None:
                continue
            original = list(planned[worker])
            replacement = self._follow_terminal_commitment(observation, worker, position, commitment)
            if replacement is None:
                if self._telemetry is not None:
                    self._telemetry.record(guard_type='terminal_commitment', worker=worker, step=step, original=original, replacement=original, detail='cancelled')
                episode.terminal.pop(worker, None)
                continue
            planned[worker] = replacement
            if self._telemetry is not None:
                self._telemetry.record(guard_type='terminal_commitment', worker=worker, step=step, original=original, replacement=replacement, detail=commitment.phase)
        if step < TERMINAL_RETURN_STEP:
            return {'farmer': planned[0], 'hands': planned[1:], 'market': action['market']}
        for worker, position in enumerate(positions):
            if worker in episode.terminal:
                continue
            inventory = _inventory(private, worker)
            if _sellable_units(inventory) > 0:
                original = list(planned[worker])
                if position in shed_tiles:
                    planned[worker] = ['DROP']
                    if self._telemetry is not None:
                        self._telemetry.record(guard_type='terminal_inventory_route', worker=worker, step=step, original=original, replacement=['DROP'])
                    continue
                target = nearest_position(position, shed_tiles)
                if distance(position, target) + 1 <= transitions:
                    replacement = step_toward(position, target, ['DROP'])
                    planned[worker] = replacement
                    if self._telemetry is not None:
                        self._telemetry.record(guard_type='terminal_inventory_route', worker=worker, step=step, original=original, replacement=replacement)
                    continue
            tile = _tile_at(farm, position)
            if _harvestable(tile):
                return_distance = min((distance(position, target) for target in shed_tiles))
                if return_distance + 2 <= transitions:
                    original = list(planned[worker])
                    planned[worker] = ['HARVEST']
                    if self._telemetry is not None:
                        self._telemetry.record(guard_type='terminal_inventory_route', worker=worker, step=step, original=original, replacement=['HARVEST'])
        return {'farmer': planned[0], 'hands': planned[1:], 'market': action['market']}

    def _find_terminal_commitment(self, observation: dict[str, Any], worker: int, position: tuple[int, int], reserved: set[tuple[int, int]]) -> TerminalCommitment | None:
        step = int(observation.get('step', 0))
        if step < TERMINAL_PLANNING_STEP:
            return None
        player = int(observation['player'])
        farm = observation['farms'][player]
        board_size = len(farm['tiles'])
        future_position = position
        trace: list[tuple[int, list[Any], tuple[int, int]]] = []
        harvest_step = None
        target = None
        for offset in range(FINAL_EXECUTABLE_STEP - step + 1):
            worker_action = self._future_action(observation, worker, offset)
            if not worker_action:
                return None
            operation = str(worker_action[0])
            trace.append((step + offset, worker_action, future_position))
            if operation == 'HARVEST':
                target = future_position
                harvest_step = step + offset
                break
            future_position = _moved(future_position, operation, board_size)
        if target is None or harvest_step is None or target in reserved:
            return None
        tile = _tile_at(farm, target)
        if not (isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (int(tile.get('yield_units', 0)) > 0)):
            return None
        needs_water = False
        for _, worker_action, action_position in trace[:-1]:
            operation = str(worker_action[0])
            if operation in MOVE_ACTIONS or operation in {'PASS', 'DROP'}:
                continue
            if operation == 'WATER' and action_position == target:
                needs_water = not bool(tile.get('watered_today', False))
                continue
            return None
        shed_tiles = _shed_access_tiles(board_size)
        shed = nearest_position(target, shed_tiles)
        baseline_return = distance(target, shed) + 1
        if baseline_return <= FINAL_EXECUTABLE_STEP - harvest_step:
            return None
        required = distance(position, target) + int(needs_water) + 1 + distance(target, shed) + 1
        available = FINAL_EXECUTABLE_STEP - step + 1
        if required > available or required < available - 1:
            return None
        return TerminalCommitment(target=target, shed=shed, needs_water=needs_water)

    def _follow_terminal_commitment(self, observation: dict[str, Any], worker: int, position: tuple[int, int], commitment: TerminalCommitment) -> list[Any] | None:
        player = int(observation['player'])
        farm = observation['farms'][player]
        private = observation['private']
        if commitment.phase == 'target':
            if position != commitment.target:
                return step_toward(position, commitment.target, PASS)
            tile = _tile_at(farm, position)
            if commitment.needs_water:
                if not (isinstance(tile, dict) and tile.get('kind') == 'PLANT' and (not tile.get('watered_today', False))):
                    return None
                commitment.needs_water = False
                return ['WATER']
            if not _harvestable(tile):
                return None
            commitment.phase = 'shed'
            return ['HARVEST']
        inventory = _inventory(private, worker)
        if _sellable_units(inventory) <= 0:
            return None
        if position == commitment.shed:
            return ['DROP']
        return step_toward(position, commitment.shed, ['DROP'])

    def _terminal_market(self, observation: dict[str, Any], action: AgentAction) -> list[list[Any]]:
        projected = _projected_shed(observation, action)
        return [['SELL', product, int(projected.get(product, 0))] for product in SELLABLE_PRODUCTS if int(projected.get(product, 0)) > 0]

def _tile_at(farm: dict[str, Any], position: tuple[int, int]) -> Any:
    x, y = position
    return farm['tiles'][y][x]

def _is_weed(tile: Any) -> bool:
    return isinstance(tile, dict) and tile.get('kind') == 'WEED'

def _is_locked(tile: Any) -> bool:
    return tile == 'LOCKED'

def _repair_has_time(observation: dict[str, Any], operation: str) -> bool:
    day = int(observation.get('day', 0))
    hour = int(observation.get('hour', 0))
    if day >= 29:
        return False
    return hour <= (21 if operation == 'PLANT' else 22)

def _moved(position: tuple[int, int], operation: str, board_size: int) -> tuple[int, int]:
    offsets = {'NORTH': (0, -1), 'SOUTH': (0, 1), 'EAST': (1, 0), 'WEST': (-1, 0)}
    if operation not in offsets:
        return position
    dx, dy = offsets[operation]
    target = (position[0] + dx, position[1] + dy)
    if 0 <= target[0] < board_size and 0 <= target[1] < board_size:
        return target
    return position

def _inventory(private: dict[str, Any], worker: int) -> dict[str, Any]:
    inventories = private.get('inventories', [])
    if worker < len(inventories) and isinstance(inventories[worker], dict):
        return inventories[worker]
    return {}

def _shed_access_tiles(board_size: int) -> tuple[tuple[int, int], ...]:
    half = board_size // 2
    return ((half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half))

def _sellable_units(inventory: dict[str, Any]) -> int:
    return sum((int(inventory.get(product, 0)) for product in SELLABLE_PRODUCTS))

def _harvestable(tile: Any) -> bool:
    return isinstance(tile, dict) and int(tile.get('yield_units', 0)) > 0

def _projected_shed(observation: dict[str, Any], action: AgentAction) -> dict[str, int]:
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    shed = {str(item): int(quantity) for item, quantity in private.get('shed', {}).items()}
    positions = [tuple(farm['farmer']), *(tuple(position) for position in farm.get('hands', []))]
    actions = [action['farmer'], *action['hands']]
    shed_tiles = set(_shed_access_tiles(len(farm['tiles'])))
    for worker, (position, worker_action) in enumerate(zip(positions, actions, strict=True)):
        if not worker_action:
            continue
        inventory = _inventory(private, worker)
        operation = str(worker_action[0])
        if operation == 'DROP' and position in shed_tiles:
            for item, quantity in inventory.items():
                room = max(0, SHED_CAPACITY - sum(shed.values()))
                deposited = min(max(0, int(quantity)), room)
                if deposited > 0:
                    shed[str(item)] = shed.get(str(item), 0) + deposited
            continue
        if operation != 'PLACE' or len(worker_action) < 2:
            continue
        item = str(worker_action[1])
        tile = _tile_at(farm, position)
        if item in ANIMAL_STRUCTURES and isinstance(tile, dict) and (tile.get('kind') == ANIMAL_STRUCTURES[item]) and (not tile.get('animal')):
            continue
        if position not in shed_tiles:
            continue
        requested = int(worker_action[2]) if len(worker_action) >= 3 else 1
        room = max(0, SHED_CAPACITY - sum(shed.values()))
        deposited = min(max(0, requested), int(inventory.get(item, 0)), room)
        if deposited > 0:
            shed[item] = shed.get(item, 0) + deposited
    return shed

def _shed_inventory(observation: dict[str, Any]) -> dict[str, int]:
    private = observation['private']
    return {str(item): int(quantity) for item, quantity in private.get('shed', {}).items() if int(quantity) > 0}

def _projected_shed_after_market(before: dict[str, int], market: list[list[Any]]) -> dict[str, int]:
    after = dict(before)
    for order in market:
        if len(order) < 3 or str(order[0]) != 'SELL':
            continue
        product = str(order[1])
        sold = int(order[2])
        if sold <= 0:
            continue
        remaining = max(0, after.get(product, 0) - sold)
        if remaining:
            after[product] = remaining
        else:
            after.pop(product, None)
    return after

def build_candidate_a_agent(*, baseline: Baseline, enable_recovery: bool=True, enable_liquidation: bool=True, enable_terminal_commitments: bool=True, telemetry: CandidateATelemetry | None=None) -> Baseline:
    executor = CandidateAExecutor(baseline, telemetry=telemetry)
    return build_residual_agent(CandidateAPolicy(enable_recovery=enable_recovery, enable_liquidation=enable_liquidation, enable_terminal_commitments=enable_terminal_commitments), baseline=baseline, executor=executor)
_DECIDE = build_candidate_a_agent(baseline=calendar)
'Candidate A: guarded recovery and liquidation over the elite calendar.'
from typing import Any

def decide(observation: dict[str, Any]) -> dict[str, Any]:
    return _DECIDE(observation)
candidate_a = decide
'Candidate B: sequential-affordability market residual over Candidate A.\n\nHypothesis: in a real batch of market orders for one turn, Candidate A\nsometimes places a SELL after a money- or shed-consuming order\n(BUY_PRODUCT/BUY_SEED/BUY_ANIMAL/HIRE/BUY_LAND) that it funds. Because the\n1.32.7 engine drains each order to completion before starting the next, a\nsell positioned after a purchase cannot fund it -- moving eligible sells\nearlier can only add cash/shed-room before later orders execute, never take\nany away, so it can only keep every previously-successful order successful\nand, sometimes, rescue one that used to fail.\n\nLive replay of Candidate A\'s real 33-episode captured record found this\npattern almost entirely in WHEAT/FERTILIZER sells trailing an unrelated\nspend (858 + 825 instances), not in premium sells (0 instances) -- so this\nmodule moves any SELL, not just the four premium products the original\ndesign brief singled out. That introduces a same-item overlap with\nBUY_PRODUCT (which only ever targets WHEAT/FERTILIZER) that the premium-only\nscope never had to consider: an exhaustive sweep over quantities and\ninventory levels found no case where every order\'s fulfilled quantity tied\nbut final money still differed -- the engine\'s "quote a buy at post-buy\ninventory" rule (built to make an unchanged-market buy/sell round-trip net\nzero) appears to make same-item reordering money-neutral whenever nothing\'s\nfulfillment changes, same as the cross-item case. That is an empirical\nfinding, not a proof, so `_is_strict_improvement` keeps a same-cost money\ncheck as a free safety net rather than assuming the invariant is airtight.\n\nThis module only ever moves a SELL, never changes what the baseline chose\nto buy -- but real replay still turned up a purchase type where *rescuing*\none is dangerous. Rescuing a HIRE is safe: Candidate A\'s own recovery\nalready re-aligns actions to the live hand count (extra/fewer hands is a\nknown, handled case). Rescuing a BUY_ANIMAL is not: the fixed calendar\nnever schedules care/feed for an animal it didn\'t plan for, and a rescued\nanimal can also fill the one pasture/coop slot the calendar\'s own later,\nalready-planned animal purchase needed. On real replay this cut both ways\nin one batch of games: a rescued HIRE gained +8578 on episode 103977950,\nwhile a rescued SHEEP purchase cost -37129 on episode 103937628 -- same\nmechanism, opposite outcome, because only one of the two purchase types has\na downstream consumer of the state it creates. So `_is_rescue_barrier`\nwalls off BUY_ANIMAL specifically: a sell may still jump HIRE/BUY_PRODUCT/\nBUY_SEED/BUY_LAND, but never crosses a BUY_ANIMAL order. BUY_SEED/BUY_LAND\nare structurally closer to BUY_PRODUCT (inert until something later\nchooses to use them, no ongoing care requirement, no capacity to block) but\nhave not been individually observed rescued in real replay either way.\n\nA prior implementation of this module (order-safe premium re-*sorting* via\npermutation search) was proven mathematically inert -- each product\'s price\ndepends only on that product\'s own running inventory, so permuting SELLs of\n*already-fixed* quantities can never change total revenue -- and was\nremoved after live replay confirmed zero of 264 eligible firings ever\nchanged anything.\n\nSecond residual, added after two live episodes (105061000, 105062726) showed\nthe same calendar turn (record 200: [BUY_PRODUCT WHEAT 16, BUY_LAND]) spend\nits way past the money a same-turn BUY_LAND needed, in both games, at both\nseats. The calendar only ever attempts BUY_LAND twice in the whole 720-step\nscript (records 122 and 200); when the second attempt is starved this way it\nis never retried, and every later scripted PLANT/WATER/HARVEST/BUILD_PASTURE\nthe calendar sends to that still-unowned quadrant reports the tile as the\nliteral string "LOCKED" and executes as a no-op for the rest of the episode\n(471 such no-ops observed in each replay). `_land_priority_ordering` moves a\nstarved BUY_LAND ahead of any HIRE/BUY_PRODUCT/BUY_SEED/BUY_ANIMAL that\nprecedes it in the same turn, but never crosses a SELL in either direction\n(a SELL only ever adds cash before land is evaluated, same reasoning as the\naffordability pass, so its position is left to that pass entirely) and never\nmoves anything if BUY_LAND was not itself starved.\n\nUnlike `_sequential_affordability_ordering`, this is not a strict-dominance\nrule: displacing a HIRE/BUY_PRODUCT/BUY_SEED/BUY_ANIMAL order can and usually\ndoes lower its fulfilled count, sometimes to zero. That is accepted on\npurpose -- an entire quadrant (LAND_PRICES[1] = 2000, ~500 remaining steps of\nextra planting/harvesting surface) is judged to dominate a partial WHEAT\nrestock or an extra hire on the turns actually observed -- rather than\nproven via the same fulfilled-count invariant the sell pass relies on. The\none thing it does inherit from that pass\'s hard-won lesson: it only ever\nreorders purchases against each other, never touches when a SELL reaches the\nshared market, so it cannot reproduce the live-opponent price-timing risk\nthat walled off BUY_ANIMAL rescues and burned the BUY_SEED live gate above.\nIt has been checked against both failing replays and the full offline test\nsuite; it has not yet been run through a fresh live-opponent paired gate the\nway the sell pass was, so treat it with the same "verify before fully\ntrusting at scale" posture that gate was built to enforce.\n\n**`_land_priority_ordering` is DISABLED by default** (opt in with\n`build_candidate_b_agent(enable_land_priority=True)`). The reason is risk,\nnot measured harm, and the distinction matters for anyone reading this later:\n\n- Instrumented measurement over 8 complete games (5752 decisions, 3408\n  non-empty market batches) found `_land_priority_ordering` changed the\n  order 3 times and `_sequential_affordability_ordering` changed it 8\n  times. The entire market layer alters roughly 1.4 decisions per game, so\n  neither rule can account for a large live rating gap in either direction.\n- The seeds 300-309 six-family gate scores 108-12 both with the rule\n  (section 8\'s original A+B gate) and without it (the later no-land run),\n  against the same 107-13 Candidate A control. That is a null result for\n  this rule, not evidence against it.\n\nSo it is switched off because it is the one residual in this module that was\nnever justified by the fulfilled-count invariant -- it deliberately sacrifices\nanother purchase -- and a rule that fires ~0.4 times per game with no measured\nbenefit is not worth an unproven tail risk. Do not describe turning it off as\n"fixing" a live regression: the measurements above cannot support that claim.\n'
import math
from typing import Any
MAX_MARKET_ORDERS = 10
TERMINAL_MARKET_STEP = 717
MARKET_I0 = 10000
PRICE_FLOOR = 1
HINGE_GAIN = 8.0
MARKET_PARAMS = {'WHEAT': (25, 400, 'sqrt', 0.8, 'log', 0.2), 'CARROT': (35, 450, 'hinge', 1.0, 'sqrt', 0.7), 'TOMATO': (60, 200, 'hinge', 0.4, 'sqrt', 0.6), 'STRAWBERRY': (120, 100, 'sqrt', 0.7, 'linear', 1.6), 'MELON': (250, 300, 'log', 0.2, 'sq', 3.6), 'EGG': (50, 332, 'hinge', 0.4, 'log', 0.2), 'MILK': (160, 122, 'sqrt', 0.6, 'linear', 1.6), 'WOOL': (200, 105, 'log', 0.2, 'sq', 3.2), 'FERTILIZER': (100, 200, 'linear', 0.4, 'linear', 0.4)}
SEED_COST = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}
ANIMAL_COST = {'GOOSE': 300, 'COW': 400, 'SHEEP': 500}
LAND_PRICES = (1000, 2000, 4000)
FARM_HAND_COST_MULT = 1
SHED_CAPACITY = 100

def _shape(function: str, value: float, scale: int) -> float:
    value = max(0.0, value)
    if function == 'linear':
        return value
    if function == 'sq':
        return value * value
    if function == 'sqrt':
        return math.sqrt(value)
    if function == 'log':
        return math.log(1.0 + value)
    if function == 'hinge':
        if not scale or scale <= 0:
            return value
        unit = value / scale
        return unit + HINGE_GAIN * max(0.0, unit - 1.0) ** 2
    return value

def _market_price(product: str, inventory: int) -> int:
    base, scale, below_function, below_target, above_function, above_target = MARKET_PARAMS[product]
    if inventory < MARKET_I0:
        function = below_function
        target = below_target
        distance = MARKET_I0 - inventory
    else:
        function = above_function
        target = above_target
        distance = inventory - MARKET_I0
    amplitude = target * base / _shape(function, scale, scale)
    signed_change = (1 if inventory < MARKET_I0 else -1) * amplitude
    return max(PRICE_FLOOR, int(round(base + signed_change * _shape(function, distance, scale))))

def _fib(n: int) -> int:
    a, b = (1, 1)
    for _ in range(n):
        a, b = (b, a + b)
    return a

def _hire_cost(hires_already_today: int) -> int:
    return FARM_HAND_COST_MULT * _fib(hires_already_today)

def _next_land_cost(unlocked_quadrant_count: int) -> int | None:
    extra = unlocked_quadrant_count - 1
    if extra < 0 or extra >= len(LAND_PRICES):
        return None
    return LAND_PRICES[extra]

def _is_sell_order(order: list[Any]) -> bool:
    return len(order) >= 3 and str(order[0]) == 'SELL' and (int(order[2]) > 0)
_RESCUE_ELIGIBLE_OPS = {'HIRE', 'BUY_PRODUCT'}

def _is_rescue_barrier(order: list[Any]) -> bool:
    """True for a spend a sell must never be moved across.

    Only HIRE and BUY_PRODUCT are trusted rescue targets; everything else
    (BUY_ANIMAL, BUY_SEED, BUY_LAND) is walled off. Captured-replay testing
    (no live opponent, opponent actions fixed regardless of our timing)
    made BUY_ANIMAL look uniquely dangerous: rescuing a SHEEP purchase cost
    -37129 relative to Candidate A on episode 103937628, because the fixed
    calendar never schedules care for an animal it didn't plan for and the
    rescue can fill the pasture/coop slot its own later purchase needed.
    But a live paired-game gate against a mirror-match opponent (which
    *does* react to shared market state, unlike a replay) showed the same
    "sell wheat before buying seed/hire" calendar turn cost -15302 and
    flipped a win to a loss via a BUY_SEED rescue alone, with BUY_ANIMAL
    already walled off -- proving the risk isn't animal-specific. It's
    shared-market timing: reordering our own trades shifts the price the
    opponent's own concurrent trades land on, an effect the isolated
    single-player safety simulation in `_simulate_orders` cannot see by
    construction. HIRE (Candidate A's own recovery already re-aligns to the
    live hand count) and BUY_PRODUCT have only shown benefit so far, in
    both replay and live-opponent testing (episode 103977950: +8578 replay;
    seed 305 vs distilled-calendar: improved margin live) -- but that is
    two spend types' worth of evidence, not proof the risk can never touch
    them too. Widen this set only against new, separately-gated evidence.
    """
    return len(order) >= 1 and str(order[0]) not in _RESCUE_ELIGIBLE_OPS and (str(order[0]) != 'SELL')

def _has_reorder_opportunity(orders: list[list[Any]]) -> bool:
    """True if a sell sits after some other, non-barrier order."""
    seen_other = False
    for order in orders:
        if _is_rescue_barrier(order):
            seen_other = False
        elif _is_sell_order(order):
            if seen_other:
                return True
        else:
            seen_other = True
    return False

def _stable_partition_sells_first(tagged_orders: list[tuple[int, list[Any]]]) -> list[tuple[int, list[Any]]]:
    """Sells-first within each run, never crossing a rescue barrier."""
    result: list[tuple[int, list[Any]]] = []
    run: list[tuple[int, list[Any]]] = []
    for item in tagged_orders:
        if _is_rescue_barrier(item[1]):
            sells = [entry for entry in run if _is_sell_order(entry[1])]
            rest = [entry for entry in run if not _is_sell_order(entry[1])]
            result.extend(sells)
            result.extend(rest)
            result.append(item)
            run = []
        else:
            run.append(item)
    sells = [entry for entry in run if _is_sell_order(entry[1])]
    rest = [entry for entry in run if not _is_sell_order(entry[1])]
    result.extend(sells)
    result.extend(rest)
    return result

def _simulate_orders(*, money: float, shed: dict[str, int], market_inventory: dict[str, int], hires_today: int, unlocked_quadrant_count: int, tagged_orders: list[tuple[int, list[Any]]]) -> tuple[float, dict[int, int]]:
    """Replay one player's own order queue in isolation.

    Mirrors the 1.32.7 engine's per-order-then-per-unit commit loop for a
    single player's queue. Ignores simultaneous opponent trading on the same
    product at the same queue position -- an approximation already relied on
    elsewhere in this module for premium pricing -- but since both the
    baseline and candidate orderings are replayed under the identical
    approximation, the comparison between them stays valid.
    """
    shed = dict(shed)
    market_inventory = dict(market_inventory)
    fulfilled: dict[int, int] = {}
    for tag, order in tagged_orders:
        fulfilled[tag] = 0
        if not order:
            continue
        op = str(order[0])
        if op in ('SELL', 'BUY_PRODUCT', 'BUY_SEED', 'BUY_ANIMAL'):
            if len(order) < 3:
                continue
            item = str(order[1])
            try:
                requested = int(order[2])
            except (TypeError, ValueError):
                continue
            if requested <= 0:
                continue
            if op == 'SELL':
                if item not in market_inventory:
                    continue
                for _ in range(requested):
                    if shed.get(item, 0) <= 0:
                        break
                    price = _market_price(item, market_inventory[item])
                    shed[item] -= 1
                    money += price
                    if price > 1:
                        market_inventory[item] += 1
                    fulfilled[tag] += 1
            elif op == 'BUY_PRODUCT':
                if item not in ('WHEAT', 'FERTILIZER') or item not in market_inventory:
                    continue
                for _ in range(requested):
                    price = _market_price(item, market_inventory[item] - 1)
                    if money < price or sum(shed.values()) >= SHED_CAPACITY:
                        break
                    money -= price
                    shed[item] = shed.get(item, 0) + 1
                    market_inventory[item] -= 1
                    fulfilled[tag] += 1
            elif op == 'BUY_SEED':
                if item not in SEED_COST:
                    continue
                price = SEED_COST[item]
                for _ in range(requested):
                    if money < price:
                        break
                    money -= price
                    fulfilled[tag] += 1
            elif op == 'BUY_ANIMAL':
                if item not in ANIMAL_COST:
                    continue
                price = ANIMAL_COST[item]
                for _ in range(requested):
                    if money < price or sum(shed.values()) >= SHED_CAPACITY:
                        break
                    money -= price
                    shed[item] = shed.get(item, 0) + 1
                    fulfilled[tag] += 1
        elif op == 'HIRE':
            cost = _hire_cost(hires_today)
            if money >= cost:
                money -= cost
                hires_today += 1
                fulfilled[tag] = 1
        elif op == 'BUY_LAND':
            cost = _next_land_cost(unlocked_quadrant_count)
            if cost is not None and money >= cost:
                money -= cost
                unlocked_quadrant_count += 1
                fulfilled[tag] = 1
    return (money, fulfilled)

def _is_strict_improvement(baseline: tuple[float, dict[int, int]], candidate: tuple[float, dict[int, int]]) -> bool:
    """True if no order lost fulfillment, and something measurably improved.

    Never reject on final money alone: a rescued purchase spends money that
    a failed purchase would have left idle, so a rescued order's fulfilled
    count rising is itself the win, regardless of leftover cash. When every
    fulfilled count ties instead, fall back to requiring strictly more
    money -- not because a same-item sell/BUY_PRODUCT overlap is known to
    produce a money difference on a fulfilled tie (see module docstring: an
    exhaustive sweep found none), but because there is no proof it never
    can, and this check is free insurance if it ever does.
    """
    baseline_money, baseline_fulfilled = baseline
    candidate_money, candidate_fulfilled = candidate
    if any((candidate_fulfilled[tag] < count for tag, count in baseline_fulfilled.items())):
        return False
    if any((candidate_fulfilled[tag] > count for tag, count in baseline_fulfilled.items())):
        return True
    return candidate_money > baseline_money

def _sequential_affordability_ordering(observation: dict[str, Any], market_orders: list[list[Any]]) -> list[list[Any]]:
    """Move sells ahead of spends they could otherwise fund.

    Never invents, drops, or resizes an order -- only reorders the exact
    batch the baseline already chose -- and only takes effect when a local
    replay proves the reordered batch strictly dominates the baseline batch
    (never a smaller fulfilled quantity on any order, never less cash when
    every order's fulfilled quantity ties).
    """
    if int(observation.get('step', 0)) >= TERMINAL_MARKET_STEP:
        return market_orders
    if not market_orders or len(market_orders) > MAX_MARKET_ORDERS:
        return market_orders
    if not _has_reorder_opportunity(market_orders):
        return market_orders
    tagged = list(enumerate(market_orders))
    candidate_tagged = _stable_partition_sells_first(tagged)
    candidate_orders = [order for _, order in candidate_tagged]
    if candidate_orders == market_orders:
        return market_orders
    market = observation.get('market', {})
    market_inventory = {str(item): int(quantity) for item, quantity in market.get('inventory', {}).items()}
    if not market_inventory:
        return market_orders
    private = observation.get('private', {})
    shed = {str(item): int(quantity) for item, quantity in private.get('shed', {}).items()}
    player = int(observation.get('player', 0))
    farms = observation.get('farms')
    if not farms or player >= len(farms):
        return market_orders
    farm = farms[player]
    money = float(farm.get('money', 0))
    hires_today = int(farm.get('hires_today', 0))
    unlocked_quadrant_count = len(farm.get('unlocked_quadrants', []))
    baseline_outcome = _simulate_orders(money=money, shed=shed, market_inventory=market_inventory, hires_today=hires_today, unlocked_quadrant_count=unlocked_quadrant_count, tagged_orders=tagged)
    candidate_outcome = _simulate_orders(money=money, shed=shed, market_inventory=market_inventory, hires_today=hires_today, unlocked_quadrant_count=unlocked_quadrant_count, tagged_orders=candidate_tagged)
    if _is_strict_improvement(baseline_outcome, candidate_outcome):
        return candidate_orders
    return market_orders
_LAND_PRIORITY_DISPLACERS = {'BUY_PRODUCT', 'BUY_SEED', 'HIRE', 'BUY_ANIMAL'}

def _is_land_order(order: list[Any]) -> bool:
    return len(order) >= 1 and str(order[0]) == 'BUY_LAND'

def _land_first_ordering(tagged_orders: list[tuple[int, list[Any]]]) -> list[tuple[int, list[Any]]]:
    """Walk each BUY_LAND order back past adjacent non-SELL spends.

    Stops the moment it hits a SELL, another BUY_LAND, or the start of the
    batch -- so this never changes a SELL's position (that stays entirely
    the affordability pass's decision) and never reorders two BUY_LAND
    orders relative to each other.
    """
    result = list(tagged_orders)
    for index in range(len(result)):
        if not _is_land_order(result[index][1]):
            continue
        insert_at = index
        while insert_at > 0 and str(result[insert_at - 1][1][0]) in _LAND_PRIORITY_DISPLACERS:
            insert_at -= 1
        if insert_at != index:
            item = result.pop(index)
            result.insert(insert_at, item)
    return result

def _land_priority_ordering(observation: dict[str, Any], market_orders: list[list[Any]]) -> list[list[Any]]:
    """Rescue a BUY_LAND a preceding same-turn spend would otherwise starve.

    Only fires when reordering flips at least one BUY_LAND order from
    failing (fulfilled 0) to succeeding (fulfilled 1) in local simulation;
    see the module docstring for why this trades a purchase's fulfilled
    count away on purpose rather than requiring it never drop.
    """
    if int(observation.get('step', 0)) >= TERMINAL_MARKET_STEP:
        return market_orders
    if not market_orders or len(market_orders) > MAX_MARKET_ORDERS:
        return market_orders
    if not any((_is_land_order(order) for order in market_orders)):
        return market_orders
    tagged = list(enumerate(market_orders))
    candidate_tagged = _land_first_ordering(tagged)
    candidate_orders = [order for _, order in candidate_tagged]
    if candidate_orders == market_orders:
        return market_orders
    market = observation.get('market', {})
    market_inventory = {str(item): int(quantity) for item, quantity in market.get('inventory', {}).items()}
    if not market_inventory:
        return market_orders
    private = observation.get('private', {})
    shed = {str(item): int(quantity) for item, quantity in private.get('shed', {}).items()}
    player = int(observation.get('player', 0))
    farms = observation.get('farms')
    if not farms or player >= len(farms):
        return market_orders
    farm = farms[player]
    money = float(farm.get('money', 0))
    hires_today = int(farm.get('hires_today', 0))
    unlocked_quadrant_count = len(farm.get('unlocked_quadrants', []))
    baseline_outcome = _simulate_orders(money=money, shed=shed, market_inventory=market_inventory, hires_today=hires_today, unlocked_quadrant_count=unlocked_quadrant_count, tagged_orders=tagged)
    candidate_outcome = _simulate_orders(money=money, shed=shed, market_inventory=market_inventory, hires_today=hires_today, unlocked_quadrant_count=unlocked_quadrant_count, tagged_orders=candidate_tagged)
    land_tags = [tag for tag, order in tagged if _is_land_order(order)]
    baseline_fulfilled = baseline_outcome[1]
    candidate_fulfilled = candidate_outcome[1]
    rescued = any((baseline_fulfilled.get(tag, 0) == 0 and candidate_fulfilled.get(tag, 0) == 1 for tag in land_tags))
    return candidate_orders if rescued else market_orders

def build_candidate_b_agent(*, baseline: Baseline=candidate_a, enable_land_priority: bool=False) -> Baseline:
    """Create Candidate A plus the market-timing residuals."""

    def decide(observation: dict[str, Any]) -> AgentAction:
        action = clone_action(baseline(observation))
        market = _sequential_affordability_ordering(observation, action['market'])
        action['market'] = _land_priority_ordering(observation, market) if enable_land_priority else market
        return action
    return decide
'Behavior clone of the strongest tape found by systematic search.\n\nSource: episode 105531280, player 1 ("Giulio Ravasio", public leaderboard\n2908.0 at capture), the winning side of a 2026-09-04 top-table game.\n\nThis is *not* the same Giulio game Candidate C2 clones. C2 uses episode\n105144807, captured 2026-09-03. This one was selected by scoring **191\ncandidate tapes** -- every side of every cached replay belonging to a team\nrated 2400+ on the game that team won -- on our own final reward across\nfixed seeds with the same guard stack. See rl/GOAL.md section 9n.\n\nWhy own-reward drove the search rather than win rate: section 9m measured\nthat win rate against frozen tapes overstates live strength by roughly\nforty points, while our own coin production is almost entirely\nself-determined (a probe showed byte-identical farm play across seeds,\nwith reward moving only through market prices). Coins transfer; tape-panel\nwin rate does not.\n\nSame open-loop mechanism as the other distilled agents: a per-step lookup\ninto the recorded action sequence, indexed `step + 1` because the action\nrecorded at replay index k was the one chosen while observing step k-1\n(verified empirically against the simulator, not assumed).\n'
import base64
import json
import zlib
from pathlib import Path
from typing import Any
GIULIO2_MODEL_PAYLOAD: str | None = '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'
PASS = ['PASS']

def _load_giulio2_actions() -> tuple[dict[str, Any], ...]:
    payload = GIULIO2_MODEL_PAYLOAD
    if payload is None:
        model = json.loads(MODEL_PATH.read_text(encoding='utf-8'))
        payload = str(model['actions_zlib_b64'])
    compressed = base64.b64decode(payload)
    actions = json.loads(zlib.decompress(compressed).decode('utf-8'))
    if len(actions) != 720:
        raise ValueError('Distilled elite-giulio2 calendar must contain 720 records')
    return tuple(actions)
GIULIO2_ACTIONS = _load_giulio2_actions()

def elite_giulio2_decide(observation: dict[str, Any]) -> dict[str, Any]:
    next_record = int(observation.get('step', 0)) + 1
    if next_record >= len(GIULIO2_ACTIONS):
        return {'farmer': PASS, 'hands': [], 'market': []}
    planned = GIULIO2_ACTIONS[next_record]
    return {'farmer': list(planned.get('farmer', PASS)), 'hands': [list(action) for action in planned.get('hands', [])], 'market': [list(order) for order in planned.get('market', [])]}
elite_giulio2_route = elite_giulio2_decide
"Candidate D: the searched-best elite route under the proven guard stack.\n\nCandidate D is not a new mechanism. Sections 9j and 9k spent a long time\nlooking for one -- glut-aware sell deferral, a price-floor throttle, eager\nselling, a C1/C2 route selector, and twelve alternative tapes -- and every\none of them measured neutral or negative. Section 9m then found why the\nsearch kept failing: the tape panel those experiments were scored on\noverstates live strength by roughly forty points, because a frozen replay\nis far weaker than the agent it was recorded from.\n\nSo Candidate D changes the one thing that measurement showed still moves:\nthe quality of the physical route, chosen by search rather than by\nassuming a high leaderboard rank implies a good tape (section 9k measured\nthat it does not -- the world #1's tape wins 6 of 24).\n\n**Selection.** 191 candidate tapes -- every side of every cached replay\nwhose team is rated 2400+, taken from a game that team won -- were scored\nwith this exact guard stack on our own final reward across fixed seeds.\nThe five best then ran 48 games each across six seeds, both seats and four\nopponents (two mid-field clones, two elite tapes). Episode 105531280\n(Giulio Ravasio, LB 2908.0) won on all three metrics at once:\n\n    candidate                     wins    mean coins   floor\n    Giulio ep105531280           38/48       108,472   51,094\n    Mater Welon ep105545969      28/48       112,794   53,645\n    peikopon ep105552428         32/48       107,097   49,999\n    Candidate C1 (fog flower)    32/48        97,043   47,364\n    Andrew Reed ep105554550      36/48        87,440   43,542\n\nIt is also balanced -- 6/12, 12/12, 8/12, 12/12 across the four opponents,\nwith no collapse against any one of them, and it is strongest exactly\nwhere C1 is weakest (8/12 against the Jesse Bullard tape, against C1's\n4/12). Mater Welon's tape earns more coins but loses 0/12 to one opponent,\nwhich is the failure mode a single frozen route can least afford.\n\nNote this is a *different game* from the one Candidate C2 clones. C2 uses\nGiulio's episode 105144807; this is 105531280, captured a day later, and\nthe two are not interchangeable -- the search scored many Giulio games and\nonly this one came out on top.\n\nThe wrapping is deliberately identical to Candidate C's, so the comparison\nisolates the route: Candidate A's guarded recovery and live terminal\nliquidation, then Candidate B's market-timing residuals with land priority\noff by default.\n"
from typing import Any

def build_candidate_d_agent(baseline: Baseline=elite_giulio2_route) -> Baseline:
    """Wrap a route in Candidate A's guards and Candidate B's residuals."""
    return build_candidate_b_agent(baseline=build_candidate_a_agent(baseline=baseline))
_DECIDE = build_candidate_d_agent()

def candidate_d_decide(observation: dict[str, Any]) -> AgentAction:
    return _DECIDE(observation)
agent = build_candidate_d_agent()
